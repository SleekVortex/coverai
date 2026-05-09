from datetime import UTC, datetime

from coverai.domain.enums import Plan
from coverai.domain.ports import (
    GenerationRequestRepo,
    MetricsRecorder,
    SubscriptionRepo,
    UserRepo,
)
from coverai.services.billing.errors import QuotaExceededError
from coverai.services.billing.models import PlanUsage
from coverai.services.billing.plan_policy import plan_limits
from coverai.services.config import SERVICE_CONFIG
from coverai.services.metrics import noop_metrics
from coverai.services.users.errors import UserNotFoundError

MOSCOW_TZ = SERVICE_CONFIG.billing.quota_timezone
QUOTA_STATUSES = set(SERVICE_CONFIG.billing.quota_statuses)


class QuotaService:
    def __init__(
        self,
        user_repo: UserRepo,
        subscription_repo: SubscriptionRepo,
        generation_request_repo: GenerationRequestRepo,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._subscription_repo = subscription_repo
        self._generation_request_repo = generation_request_repo
        self._metrics = metrics or noop_metrics

    async def get_plan_usage(
        self,
        user_id: int,
        now: datetime | None = None,
    ) -> PlanUsage:
        """Возвращает использование тарифа."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        current_time = now or datetime.now(UTC)
        limits = plan_limits(user.plan)
        subscription = await self._subscription_repo.get_active_by_user_id(user_id)

        if limits.limit is None:
            usage = PlanUsage(
                plan=user.plan,
                used=0,
                limit=None,
                period=None,
                period_start=None,
                subscription_expires_at=(
                    subscription.expires_at if subscription else None
                ),
            )
            self._metrics.set_quota_usage(usage.plan, usage.used, usage.limit)
            return usage

        period_start = _quota_period_start(user.plan, current_time)
        used = await self._generation_request_repo.count_by_user_statuses_since(
            user_id=user_id,
            statuses=QUOTA_STATUSES,
            since=period_start,
        )

        usage = PlanUsage(
            plan=user.plan,
            used=used,
            limit=limits.limit,
            period=limits.period,
            period_start=period_start,
            subscription_expires_at=subscription.expires_at if subscription else None,
        )
        self._metrics.set_quota_usage(usage.plan, usage.used, usage.limit)
        return usage

    async def ensure_can_generate(
        self,
        user_id: int,
        now: datetime | None = None,
    ) -> PlanUsage:
        """Проверяет доступность генерации."""
        usage = await self.get_plan_usage(user_id, now)
        if usage.limit is not None and usage.used >= usage.limit:
            raise QuotaExceededError

        return usage

    async def reserve_generation_request(
        self,
        user_id: int,
        now: datetime | None = None,
    ) -> PlanUsage:
        """Резервирует запрос генерации."""
        return await self.ensure_can_generate(user_id, now)


def _quota_period_start(plan: Plan, now: datetime) -> datetime:
    local_now = now.astimezone(MOSCOW_TZ)
    if plan == Plan.FREE:
        return local_now.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ).astimezone(UTC)
    if plan == Plan.STANDARD:
        return local_now.replace(
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ).astimezone(UTC)

    return local_now.astimezone(UTC)
