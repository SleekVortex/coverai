from typing import Protocol, runtime_checkable

from coverai.domain.enums import Plan
from coverai.domain.read_models import (
    AdminAnalyticsOverviewRead,
    AdminUserDetailRead,
    AdminUserSummaryRead,
    BillingSummaryRead,
    CreditTransactionRead,
    UserAnalyticsRead,
)


@runtime_checkable
class BillingReadRepo(Protocol):
    async def billing_summary(
        self,
        user_id: int,
        recent_limit: int = 5,
    ) -> BillingSummaryRead:
        """Возвращает баланс и последние транзакции."""
        ...

    async def transactions(self, user_id: int) -> list[CreditTransactionRead]:
        """Возвращает транзакции пользователя."""
        ...


@runtime_checkable
class AnalyticsReadRepo(Protocol):
    async def user_usage(self, user_id: int) -> UserAnalyticsRead:
        """Возвращает пользовательскую аналитику."""
        ...


@runtime_checkable
class AdminReadRepo(Protocol):
    async def list_users(
        self,
        limit: int,
        offset: int,
        plan: Plan | None,
        role: str | None,
    ) -> list[AdminUserSummaryRead]:
        """Возвращает пользователей для админки."""
        ...

    async def user_detail(self, user_id: int) -> AdminUserDetailRead | None:
        """Возвращает детали пользователя для админки."""
        ...

    async def analytics_overview(self) -> AdminAnalyticsOverviewRead:
        """Возвращает административную аналитику."""
        ...

