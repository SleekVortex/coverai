import logging
import re

TELEGRAM_BOT_URL_PATTERN = re.compile(r"(https://api\.telegram\.org/bot)[^/\s]+")


class SecretRedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        """Фильтрует запись лога."""
        record.msg = redact_log_secrets(record.getMessage())
        record.args = ()
        return True


def configure_logging(level: str) -> None:
    """Настраивает logging."""
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    for handler in logging.getLogger().handlers:
        handler.addFilter(SecretRedactionFilter())


def redact_log_secrets(message: str) -> str:
    """Маскирует секреты в логах."""
    return TELEGRAM_BOT_URL_PATTERN.sub(r"\1<redacted>", message)
