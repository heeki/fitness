from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import ClassVar

class ServerSettings(BaseSettings):
    """Settings for the Strava MCP server."""
    model_config = SettingsConfigDict(env_prefix="STRAVA_")

    # server settings from environment variables if set, otherwise use pre-set defaults
    host: str = "0.0.0.0"
    port: int = 8000
    stateless_http: bool = True
    debug: bool = False
    client_id: str = ""
    client_secret: str = ""
    url_authorize: str = "https://www.strava.com/oauth/authorize"
    url_token: str = "https://www.strava.com/oauth/token"

    def __init__(self, **data):
        """Initialize settings with values from environment variables."""
        super().__init__(**data)
