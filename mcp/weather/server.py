import click
import json
import logging
import os
from fastapi import FastAPI
from langfuse import Langfuse
from langfuse.decorators import observe
from typing import Dict, Any, List
from mcp.server.fastmcp import FastMCP
from meteo import Meteo

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

# setup mcp
mcp = FastMCP("weather")

@mcp.tool()
@observe()
def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    timezone: str
) -> List[Dict[str, Any]]:
    """
    Retrieve historical weather data for a given latitude and longitude using OpenWeatherMap History API.
    Args:
        latitude: latitude
        longitude: longitude
        start_date: start date
        end_date: end date
        timezone: timezone, e.g. "America/New_York"
    Returns:
        List of objects from OpenMeteo Historical Weather API
    """
    meteo = Meteo()
    try:
        records = meteo.get_hourly_data(latitude, longitude, start_date, end_date, timezone)
        return records
    except Exception as e:
        return [{"error": str(e)}]

@mcp.custom_route("/ping", methods=["GET"])
@observe()
def ping():
    return {"status": "ok"}

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
    start_message = f"Configured server in {transport} mode"
    start_message += f" on {host}:{port}" if transport != "stdio" else ""
    print(start_message)

    match transport:
        case 'stdio' | 'streamable-http':
            mcp.run(transport=transport)
        case _:
            import uvicorn
            app = FastAPI(
                title="Weather",
                lifespan=lambda app: mcp.session_manager.run(),
            )
            app.mount("/weather", mcp.streamable_http_app())
            uvicorn.run(app, host=host, port=port, log_level="info")
    return 0

if __name__ == "__main__":
    main()