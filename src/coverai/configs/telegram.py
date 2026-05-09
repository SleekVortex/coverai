from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class TelegramSettings(BaseSettings):
    model_config = CONFIG_MODEL

    bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    proxy_url: str = Field(default="", alias="TELEGRAM_PROXY_URL")

