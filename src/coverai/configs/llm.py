from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings

from coverai.configs.base import CONFIG_MODEL


class LLMSettings(BaseSettings):
    model_config = CONFIG_MODEL

    api_key: str = Field(
        default="",
        validation_alias=AliasChoices("LLM_API_KEY", "OPENROUTER_API_KEY"),
    )
    base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        validation_alias=AliasChoices("LLM_BASE_URL", "OPENROUTER_BASE_URL"),
    )
    model: str = Field(
        default="deepseek/deepseek-chat-v3.2",
        validation_alias=AliasChoices("LLM_MODEL", "PRIMARY_LLM_MODEL"),
    )
    proxy_url: str = Field(default="", alias="LLM_PROXY_URL")
