from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime:
        """Возвращает текущее время."""
        ...


class SystemClock:
    def now(self) -> datetime:
        """Возвращает текущее время."""
        return datetime.now(UTC)
