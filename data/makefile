include etc/environment.sh

inspector:
	mcp dev src/inspector.py

strava.oauth.code:
	uv run src/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET}
strava.oauth.accesstoken:
	uv run src/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET} --code ${STRAVA_AUTH_CODE} | jq
strava.oauth.refresh:
	uv run src/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET} --refresh-token ${STRAVA_REFRESH_TOKEN} | jq
strava.oauth.activities:
	uv run src/strava/retrieve_tokens.py --client-id ${STRAVA_CLIENT_ID} --client-secret ${STRAVA_CLIENT_SECRET} --access-token ${STRAVA_ACCESS_TOKEN} | jq

strava.stdio:
	uv run src/strava/server.py --transport stdio
strava.streamable-http:
	uv run src/strava/server.py --transport streamable-http
strava.fastapi:
	uv run src/strava/server.py --transport fastapi

agent:
	uv run src/agent.py