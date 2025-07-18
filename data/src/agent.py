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
mcp_server_settings = StdioServerParameters(
        command='uv',
        args=['run', 'src/strava/server.py', '--transport', 'stdio'],
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
    lambda: stdio_client(mcp_server_settings)
)
system_prompt = dedent(f"""
    You are a helpful assistant that can retrieve data as part of a larger fitness plan coordinator application. You can use the Strava API to get information about the user's running and weight training activities. In order to interact with the Strava API, you will need to ensure that the client id, client secret, and access token are set in the environment variables and are passed to the get_activities tool as parameters.
    [IMPORTANT] You must not hallucinate these credentials, as that will result in failed calls to the Strava API endpoint.
    """
)

async def main():
    try:
        with strava_client_stdio:
            strava_tools = strava_client_stdio.list_tools_sync()
            agent = Agent(
                system_prompt=system_prompt,
                model=bedrock_model,
                tools=strava_tools,
                callback_handler=None
            )
            prompt = 'Summarize the last four weeks of my Strava activities.'
            result = agent.stream_async(prompt)
            async for chunk in result:
                if 'data' in chunk:
                    print(chunk['data'], end='', flush=True)
                elif 'current_tool_use' in chunk and chunk.get('current_tool_use').get('name'):
                    print(chunk['current_tool_use']['name'])
    except botocore.exceptions.EventStreamError as e:
        logging.error(f"\nEventStreamError: {e}")
    except botocore.exceptions.ReadTimeoutError as e:
        logging.error(f"\nReadTimeoutError: {e}")
    except Exception as e:
        logging.error(f"\nError: {e}")

if __name__ == "__main__":
    asyncio.run(main())
