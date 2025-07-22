include etc/environment.sh

strava.oauth.code:
	uv run mcp/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET}
strava.oauth.accesstoken:
	uv run mcp/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET} --code ${STRAVA_AUTH_CODE} | jq
strava.oauth.refresh:
	uv run mcp/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET} --refresh-token ${STRAVA_REFRESH_TOKEN} | jq
strava.oauth.activities:
	uv run mcp/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET} --access-token ${STRAVA_ACCESS_TOKEN} | jq

inspector:
	mcp dev mcp/inspector.py

strava.stdio:
	uv run mcp/strava/server.py --transport stdio
strava.streamable-http:
	uv run mcp/strava/server.py --transport streamable-http
strava.fastapi:
	uv run mcp/strava/server.py --transport fastapi

meteo:
	uv run mcp/weather/meteo.py
agent:
	uv run agents/activity/agent.py