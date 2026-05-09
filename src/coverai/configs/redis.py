from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class RedisSettings(BaseSettings):
    model_config = CONFIG_MODEL

    url: str = Field(default="redis://redis:6379/0", alias="REDIS_URL")

