import asyncio
import boto3
import botocore
import logging
import os
from mcp import stdio_client, StdioServerParameters
from strands import Agent
from strands.models import BedrockModel
from strands.tools.mcp import MCPClient
from textwrap import dedent

# constants
READ_TIMEOUT = 300
CONNECT_TIMEOUT = 60
MAX_ATTEMPTS = 3
BEDROCK_MODEL_ID = 'us.anthropic.claude-3-7-sonnet-20250219-v1:0'
TEMPERATURE = 0.1

# logging initialization
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s (%(name)s) [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)

# aws initialization
session = boto3.session.Session(region_name='us-east-1')
# bedrock_client = session.client('bedrock-runtime')
bedrock_model = BedrockModel(
    model_id=BEDROCK_MODEL_ID,
    temperature=TEMPERATURE,
    boto_client_config=boto3.session.Config(
        read_timeout=READ_TIMEOUT,
        connect_timeout=CONNECT_TIMEOUT,
        retries={'max_attempts': MAX_ATTEMPTS}
    )
)

# mcp and agent initialization
strava_server_settings = StdioServerParameters(
        command='uv',
        args=['run', 'mcp/strava/server.py', '--transport', 'stdio'],
        env={
            'LANGFUSE_HOST': os.getenv('LANGFUSE_HOST'),
            'LANGFUSE_PUBLIC_KEY': os.getenv('LANGFUSE_PUBLIC_KEY'),
            'LANGFUSE_SECRET_KEY': os.getenv('LANGFUSE_SECRET_KEY'),
            'STRAVA_CLIENT_ID': os.getenv('STRAVA_CLIENT_ID'),
            'STRAVA_CLIENT_SECRET': os.getenv('STRAVA_CLIENT_SECRET'),
            'STRAVA_ACCESS_TOKEN': os.getenv('STRAVA_ACCESS_TOKEN')
        }
    )
strava_client_stdio = MCPClient(
    lambda: stdio_client(strava_server_settings)
)

weather_server_settings = StdioServerParameters(
    command='uv',
    args=['run', 'mcp/weather/server.py', '--transport', 'stdio'],
    env={
        'LANGFUSE_HOST': os.getenv('LANGFUSE_HOST'),
        'LANGFUSE_PUBLIC_KEY': os.getenv('LANGFUSE_PUBLIC_KEY'),
        'LANGFUSE_SECRET_KEY': os.getenv('LANGFUSE_SECRET_KEY')
    }
)
weather_client_stdio = MCPClient(
    lambda: stdio_client(weather_server_settings)
)

system_prompt = dedent(f"""
    You are a helpful assistant that can retrieve data as part of a larger fitness plan coordinator application. You can use the Strava API to get information about the user's running and weight training activities. In order to interact with the Strava API, you will need to ensure that the client id, client secret, and access token are set in the environment variables and are passed to the get_activities tool as parameters.
    [IMPORTANT] You must not hallucinate these credentials, as that will result in failed calls to the Strava API endpoint.

    For gathering data, use the following guidelines:
    1/ If needed, pull multiple pages of activitie from Strava to ensure that you have enough data to capture all the activities of the requested time period.
    2/ Get weather information for the location of each run and include it in the weekly summaries.

    For gathering weather information:
    1/ Parse start_latlng from Strava activities to extract the latitude and longitude parameters.
    2/ Use start_date_local from Strava activities for both the start_date and end_date parameters, using only YYYY-MM-DD format.
    [IMPORTANT] Be sure to strip the time component off of the start_date_local value, after the T, e.g. 2025-07-21T07:40:35Z -> 2025-07-21.
    3/ Use the timezone from Strava activities as the timezone parameter, usign only TZ identifiers, e.g. America/New_York.
    [IMPORTANT] If the weather tool returns an error, print out error messages and continue with the next activity.

    For calculating weekly summaries:
    1/ When calculating the weekly summary, start on the Monday and conclude on the Sunday. Each week should be a contiguous set of days and should not run into the next week. Specifically, the last day of the week should be a Sunday, not the following Monday.
    2/ Start with the oldest week and work your way to the current week.
    3/ Include only the requested number of weeks in the weekly summaries.
    4/ Include the total number of activities, total distance run, total time in active running, and average heart rate per run.
    5/ Include summaries of each run in the weekly summaries along with the weather information for the location of the run.
    6/ Exclude any activities that are not running.
    [IMPORTANT] Days should not overlap between weeks to prevent double counting.

    For providing the final summary:
    1/ Include relevant patterns and observations about the data.
    2/ Include observations about how weather conditions may have affected the runs.
    """
)

async def main():
    try:
        with strava_client_stdio, weather_client_stdio:
            strava_tools = strava_client_stdio.list_tools_sync()
            weather_tools = weather_client_stdio.list_tools_sync()
            all_tools = strava_tools + weather_tools
            agent = Agent(
                system_prompt=system_prompt,
                model=bedrock_model,
                tools=all_tools,
                callback_handler=None
            )
            prompt = "Summarize the last six weeks of my Strava activities and include the weather information for each run."
            result = agent.stream_async(prompt)
            async for chunk in result:
                if 'data' in chunk:
                    print(chunk['data'], end='', flush=True)
    except botocore.exceptions.EventStreamError as e:
        logging.error(f"\nEventStreamError: {e}")
    except botocore.exceptions.ReadTimeoutError as e:
        logging.error(f"\nReadTimeoutError: {e}")
    except Exception as e:
        logging.error(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
