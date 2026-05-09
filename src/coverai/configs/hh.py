from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class HHSettings(BaseSettings):
    model_config = CONFIG_MODEL

    access_token: str = Field(default="", alias="HH_ACCESS_TOKEN")
    user_agent: str = Field(default="coverai/0.1.0", alias="HH_USER_AGENT")
    proxy_url: str = Field(default="", alias="HH_PROXY_URL")
    html_fallback_enabled: bool = Field(
        default=True,
        alias="HH_HTML_FALLBACK_ENABLED",
    )

