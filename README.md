# Agent-enabled Fitness Coordinator Application

A comprehensive fitness data analysis system that combines AI agents with external APIs to analyze Strava activities and weather data. The system uses Model Context Protocol (MCP) servers to integrate Strava API and weather data, enabling AI agents to retrieve and analyze fitness activities with environmental context.

## Overview

This project implements an AI agent architecture that can:
- Retrieve and analyze Strava fitness activities
- Gather historical weather data for activity locations
- Generate weekly summaries with weather correlation
- Provide insights on how weather conditions affect performance

The system is built using:
- **Strands Agents**: AI agent framework with Bedrock integration
- **Model Context Protocol (MCP)**: For tool integration
- **FastMCP**: FastAPI-based MCP server implementation
- **Langfuse**: Observability and tracing
- **OpenMeteo**: Historical weather data API

## Project Structure

```
fitness/
├── agents/                     # AI agent implementations
│   ├── activity/               # Strava activity analysis agent
│   │   └── agent.py            # Main agent with Bedrock integration
│   └── coordinator/            # Future coordinator agents
├── mcp/                        # Model Context Protocol servers
│   ├── strava/                 # Strava API integration
│   │   ├── server.py           # MCP server for Strava API
│   │   ├── strava_oauth.py     # OAuth authentication
│   │   ├── strava_analyzer.py  # Activity analysis tools
│   │   ├── retrieve_tokens.py  # Token management
│   │   └── server_settings.py  # Server configuration
│   ├── weather/                # Weather data integration
│   │   ├── server.py           # MCP server for weather API
│   │   └── meteo.py            # OpenMeteo API client
│   ├── inspector.py            # MCP server inspection tool
│   └── routes/                 # Additional MCP routes
├── etc/                        # Configuration files
│   └── environment.sh          # Environment variables
├── main.py                     # Entry point
├── makefile                    # Build and run commands
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project metadata
└── README.md                   # This file
```

## Components

### AI Agents (`agents/`)

**Activity Agent** (`agents/activity/agent.py`)
- Uses AWS Bedrock (Claude 3.5 Sonnet) for analysis
- Integrates with Strava and Weather MCP servers
- Generates weekly activity summaries with weather correlation
- Analyzes patterns and weather impact on performance

### MCP Servers (`mcp/`)

**Strava Server** (`mcp/strava/server.py`)
- Provides tools for Strava API integration
- Handles OAuth authentication and token management
- Supports activity retrieval and analysis
- Multiple transport protocols: stdio, streamable-http, fastapi

**Weather Server** (`mcp/weather/server.py`)
- Integrates with OpenMeteo API for historical weather data
- Provides weather data for activity locations
- Supports multiple transport protocols

### Configuration (`etc/`)

**Environment Configuration** (`etc/environment.sh`)
- Langfuse observability settings
- Strava OAuth credentials
- Weather API configuration
- MCP server settings

## Running the System

### Prerequisites

1. **Python 3.12+** with `uv` package manager
2. **AWS Bedrock** access configured
3. **Strava API** credentials
4. **Langfuse** account (optional, for observability)

### Environment Setup

1. Copy the environment configuration template into your own file and update the values accordingly:
```bash
cp etc/environment.template etc/environment.sh
```

2. Install dependencies:
```bash
uv pip install -r requirements.txt
```

### Running Components

#### MCP Servers

If you want to run and test the MCP servers locally, use the following commands.

**Strava Server:**
```bash
# Stdio transport (for agent integration)
make strava.stdio

# HTTP transport
make strava.streamable-http

# FastAPI transport
make strava.fastapi
```

**Weather Server:**
```bash
# Stdio transport (for agent integration)
make meteo.stdio

# HTTP transport
make meteo.streamable-http

# FastAPI transport
make meteo.fastapi
```

#### OAuth Management

The following is used for retrieving temporary credentials from the Strava API. It assumes API access has already been setup. After retrieving the access token, the `etc/environment.sh` file needs to be updated with the latest token: `STRAVA_ACCESS_TOKEN`. Note that this is for local prototyping and testing, as the codebase needs to be udpated to take this at runtime, which is a backlog item.

**Strava OAuth workflow:**
```bash
# Get authorization code
make strava.oauth.code

# Exchange code for access token
make strava.oauth.accesstoken

# Refresh access token
make strava.oauth.refresh

# Test activities retrieval
make strava.oauth.activities
```


#### AI Agent

**Run the activity analysis agent:**
```bash
make agent
```

This will:
1. Connect to Strava and Weather MCP servers
2. Retrieve the last 6 weeks of activities
3. Gather weather data for each activity location
4. Generate weekly summaries with weather correlation
5. Provide insights on patterns and weather impact

#### Development Tools

**MCP Inspector:**
```bash
make inspector
```

**Weather Data Test:**
```bash
make meteo
```

### Available Make Commands

- `make strava.oauth.code` - Get Strava authorization code
- `make strava.oauth.accesstoken` - Exchange code for access token
- `make strava.oauth.refresh` - Refresh access token
- `make strava.oauth.activities` - Test activities retrieval
- `make inspector` - Run MCP inspector
- `make strava.stdio` - Run Strava server in stdio mode
- `make strava.streamable-http` - Run Strava server in HTTP mode
- `make strava.fastapi` - Run Strava server in FastAPI mode
- `make meteo` - Test weather data retrieval
- `make agent` - Run the activity analysis agent

