from functools import lru_cache
from typing import Any, Final

from coverai.configs.admin import AdminSettings
from coverai.configs.app import AppSettings
from coverai.configs.auth import AuthSettings
from coverai.configs.billing import BillingSettings
from coverai.configs.database import DatabaseSettings
from coverai.configs.hh import HHSettings
from coverai.configs.llm import LLMSettings
from coverai.configs.metrics import MetricsSettings
from coverai.configs.redis import RedisSettings
from coverai.configs.telegram import TelegramSettings

_UNSET: Final = object()


class Settings:
    def __init__(self, _env_file: object = _UNSET, **values: Any) -> None:
        section_values = dict(values)
        if _env_file is not _UNSET:
            section_values["_env_file"] = _env_file

        self.admin = AdminSettings(**section_values)
        self.app = AppSettings(**section_values)
        self.auth = AuthSettings(**section_values)
        self.billing = BillingSettings(**section_values)
        self.database = DatabaseSettings(**section_values)
        self.hh = HHSettings(**section_values)
        self.llm = LLMSettings(**section_values)
        self.metrics = MetricsSettings(**section_values)
        self.redis = RedisSettings(**section_values)
        self.telegram = TelegramSettings(**section_values)


@lru_cache
def get_settings() -> Settings:
    """Возвращает настройки приложения."""
    return Settings()

