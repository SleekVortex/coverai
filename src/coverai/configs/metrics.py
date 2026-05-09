from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class MetricsSettings(BaseSettings):
    model_config = CONFIG_MODEL

    enabled: bool = Field(default=True, alias="METRICS_ENABLED")
    bot_port: int = Field(default=8000, alias="BOT_METRICS_PORT")
    worker_port: int = Field(default=8001, alias="WORKER_METRICS_PORT")

