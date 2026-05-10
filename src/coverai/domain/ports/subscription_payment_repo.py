from typing import Protocol, runtime_checkable

from coverai.domain.enums import Plan
from coverai.domain.read_models import SubscriptionPaymentRead


@runtime_checkable
class SubscriptionPaymentRepo(Protocol):
    async def create(
        self,
        user_id: int,
        plan: Plan,
        amount_rub: int,
        external_id: str,
    ) -> SubscriptionPaymentRead:
        """Создает платежное намерение подписки."""
        ...

