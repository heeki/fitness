import click
import logging
import os
from fastapi import FastAPI
from langfuse import Langfuse
from langfuse.decorators import observe
from mcp.server.fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import Response
from typing import Dict, Any, Optional, List
from server_settings import ServerSettings
from strava_oauth import StravaOAuth
from strava_analyzer import StravaAnalyzer

# configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s (%(name)s) [%(levelname)s] %(message)s'
)

# initialization
logger = logging.getLogger(__name__)
langfuse = Langfuse(
    host=os.getenv("LANGFUSE_HOST"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY")
)

# helper functions
def print_debug_info(settings: ServerSettings):
    logger.info("=== debug: environment variables ===")
    langfuse_vars = {k: v for k, v in os.environ.items() if k.startswith('LANGFUSE_')}
    if langfuse_vars:
        for key, value in langfuse_vars.items():
            logger.info(f"  {key} = {value}")
    else:
        logger.warning("No LANGFUSE_ environment variables found!")
    mcp_strava_vars = {k: v for k, v in os.environ.items() if k.startswith('STRAVA_')}
    if mcp_strava_vars:
        for key, value in mcp_strava_vars.items():
            logger.info(f"  {key} = {value}")
    else:
        logger.warning("No STRAVA_ environment variables found!")

    logger.info("=== debug: settings ===")
    logger.info(f"  host = {settings.host}")
    logger.info(f"  port = {settings.port}")
    logger.info(f"  debug = {settings.debug}")
    logger.info(f"  stateless_http = {settings.stateless_http}")
    logger.info(f"  client_id = {settings.client_id}")
    logger.info(f"  client_secret = {'*' * len(settings.client_secret) if settings.client_secret else 'None'}")
    logger.info(f"  url_authorize = {settings.url_authorize}")
    logger.info(f"  url_token = {settings.url_token}")

def create_mcp_server(host: str, port: int) -> FastMCP:
    """Create and configure the FastMCP server with the given host and port."""
    settings = ServerSettings()
    settings.host = host or settings.host
    settings.port = port or settings.port
    mcp = FastMCP(
        "strava",
        host=settings.host,
        port=settings.port,
        stateless_http=settings.stateless_http,
        debug=settings.debug
    )
    @mcp.tool()
    @observe()
    def hello_world() -> Dict[str, Any]:
        """Hello world tool"""
        return {"message": "Hello world!"}

    @mcp.tool()
    @observe()
    def get_activities(
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        endpoint: str = "https://www.strava.com/api/v3/athlete/activities"
    ) -> List[Dict[str, Any]]:
        """Strava API tool
        1/ This tool can be used to get running activities from Strava using OAuth credentials
        2/ Because Strava only supports authentication code flows, the tool assumes that the auth code has already been exchanged for an access token and that the client id, client secret, and access token will either be available in the environment or be passed to the tool as arguments.
        3/ This tool also takes as an argument the endpoint to call, which will target the Strava API endpoint at https://www.strava.com/api/v3/athlete/activities by default.
        4/ This tool can also retrieve paginated results at the same endpoint by passing the 'page' and 'per_page' parameters. Retrieving paginated results is useful when the user wants to get a large number of activities.
        5/ This tool will return a JSON response from the Strava API or an error message if the request fails.
        6/ This tool can optionally return the list of activities in CSV format if the user requests it for spreadsheet analysis.

        Args:
            client_id: Strava client ID (optional, can be set via STRAVA_CLIENT_ID env var)
            client_secret: Strava client secret (optional, can be set via STRAVA_CLIENT_SECRET env var)
            access_token: Strava access token (optional, can be set via STRAVA_ACCESS_TOKEN env var)
            endpoint: Strava API endpoint to call (defaults to activities endpoint)

        Returns:
            JSON response from Strava API or error message
        """
        try:
            # get credentials from environment variables if not provided as arguments
            client_id = client_id or os.getenv('STRAVA_CLIENT_ID')
            client_secret = client_secret or os.getenv('STRAVA_CLIENT_SECRET')
            access_token = access_token or os.getenv('STRAVA_ACCESS_TOKEN')
            settings.client_id = client_id or settings.client_id
            settings.client_secret = client_secret or settings.client_secret
            # print_debug_info(settings)

            # validate that we have all required credentials
            if not all([client_id, client_secret, access_token]):
                missing = []
                if not client_id:
                    missing.append("client_id")
                if not client_secret:
                    missing.append("client_secret")
                if not access_token:
                    missing.append("access_token")
                return {
                    "error": f"Missing required credentials: {', '.join(missing)}. "
                            "Please provide them either as arguments or set the corresponding environment variables: "
                            "STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_ACCESS_TOKEN"
                }

            # initialize class with client credentials
            strava = StravaOAuth(client_id, client_secret)

            # make authenticated request
            logger.info(f"Making authenticated request to {endpoint} with access token {access_token}")
            payload = strava.make_authenticated_request(access_token, 'GET', endpoint)
            # logger.info(f"Received payload: {payload}")
            return payload

        except Exception as e:
            return {"error": str(e)}

    @mcp.tool()
    @observe()
    def summarize_activities(
        activities: List[Dict[str, Any]],
        include_weekly: bool = True
    ) -> Dict[str, Any]:
        """Summarize Strava activities with statistics and optional weekly breakdowns

        This tool takes a list of activities and provides:
        1. Overall summary statistics including total distance, time, and activity types
        2. Optional weekly breakdowns of the same statistics
        3. All distances are converted to miles and times to hours
        4. Activities are cleaned by removing unnecessary fields and converting units

        Args:
            activities: List of activity dictionaries from Strava API
            include_weekly: Whether to include weekly summaries (default: True)

        Returns:
            Dictionary containing:
            - overall: Overall statistics across all activities
            - weekly: (optional) Weekly breakdowns of statistics
        """
        try:
            analyzer = StravaAnalyzer()
            summary = analyzer.get_activities_summary(activities, include_weekly)
            return summary
        except Exception as e:
            return {"error": str(e)}

    @mcp.custom_route("/ping", methods=["GET"])
    @observe()
    def ping(request: Request) -> Response:
        """Handle health check pings."""
        return Response(status_code=200, content="pong")

    return mcp, settings

# main
@click.command()
@click.option("--host", help="host for FastAPI server (default: 0.0.0.0)")
@click.option("--port", help="port for FastAPI server (default: 8000)")
@click.option(
    "--transport",
    default="streamable-http",
    type=click.Choice(["stdio", "streamable-http", "fastapi"]),
    help="transport protocol to use: stdio, streamable-http, fastapi (default: fastapi))",
)
def main(host: str, port: int, transport: str) -> int:
    mcp, settings = create_mcp_server(host, port)
    start_message = f"Configured server in {transport} mode"
    start_message += f" on {settings.host}:{settings.port}" if transport != "stdio" else ""
    logger.info(start_message)
    print(start_message)

    match transport:
        case 'stdio' | 'streamable-http':
            mcp.run(transport=transport)
        case _:
            import uvicorn
            app = FastAPI(
                title="Strava",
                lifespan=lambda app: mcp.session_manager.run(),
            )
            app.mount("/strava", mcp.streamable_http_app())
            uvicorn.run(app, host=host, port=port, log_level="info")
    return 0

if __name__ == "__main__":
    main()