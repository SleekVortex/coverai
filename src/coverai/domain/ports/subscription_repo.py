from datetime import datetime
from typing import Protocol, runtime_checkable

from coverai.domain.entities import Subscription
from coverai.domain.enums import SubscriptionStatus


@runtime_checkable
class SubscriptionRepo(Protocol):
    async def create(self, subscription: Subscription) -> Subscription:
        """Создает запись."""
        ...

    async def get_active_by_user_id(self, user_id: int) -> Subscription | None:
        """Возвращает активную подписку."""
        ...

    async def update_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
    ) -> Subscription | None:
        """Обновляет статус записи."""
        ...

    async def list_active_expired_before(self, now: datetime) -> list[Subscription]:
        """Возвращает истекшие активные подписки."""
        ...
