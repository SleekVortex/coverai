from dataclasses import dataclass
from datetime import datetime

from coverai.domain.enums import Plan
from coverai.domain.promocodes import PromoCode


@dataclass(frozen=True, slots=True)
class PlanLimits:
    plan: Plan
    limit: int | None
    period: str | None


@dataclass(frozen=True, slots=True)
class PlanUsage:
    plan: Plan
    used: int
    limit: int | None
    period: str | None
    period_start: datetime | None
    subscription_expires_at: datetime | None

    @property
    def is_unlimited(self) -> bool:
        """Проверяет безлимитный тариф."""
        return self.limit is None

    @property
    def remaining(self) -> int | None:
        """Возвращает остаток лимита."""
        if self.limit is None:
            return None

        return max(self.limit - self.used, 0)


@dataclass(frozen=True, slots=True)
class PromoRedemptionResult:
    promo: PromoCode
    message: str
