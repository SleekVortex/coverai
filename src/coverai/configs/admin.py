from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class AdminSettings(BaseSettings):
    model_config = CONFIG_MODEL

    email: str = Field(default="admin@example.test", alias="ADMIN_EMAIL")
    password: str = Field(default="admin", alias="ADMIN_PASSWORD")

