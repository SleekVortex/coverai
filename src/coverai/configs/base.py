from pydantic_settings import SettingsConfigDict

CONFIG_MODEL = SettingsConfigDict(
    env_file=".env",
    env_file_encoding="utf-8",
    extra="ignore",
)

