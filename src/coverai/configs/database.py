from pydantic import Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class DatabaseSettings(BaseSettings):
    model_config = CONFIG_MODEL

    postgres_db: str = Field(default="coverai", alias="POSTGRES_DB")
    postgres_user: str = Field(default="coverai", alias="POSTGRES_USER")
    postgres_password: str = Field(default="coverai", alias="POSTGRES_PASSWORD")
    url: str = Field(
        default="postgresql+asyncpg://coverai:coverai@postgres:5432/coverai",
        alias="DATABASE_URL",
    )

