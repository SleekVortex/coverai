from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class AppSettings(BaseSettings):
    model_config = CONFIG_MODEL

    env: str = Field(default="local", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="Europe/Moscow", alias="TIMEZONE")

