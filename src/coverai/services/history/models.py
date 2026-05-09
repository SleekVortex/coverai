from dataclasses import dataclass
from datetime import datetime

from coverai.domain.entities import CoverLetter
from coverai.services.config import SERVICE_CONFIG

STANDARD_HISTORY_PERIOD = SERVICE_CONFIG.history.standard_history_period
DEFAULT_HISTORY_LIMIT = SERVICE_CONFIG.history.default_history_limit


@dataclass(frozen=True, slots=True)
class HistoryResult:
    letters: list[CoverLetter]
    cutoff: datetime | None
