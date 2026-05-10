from datetime import datetime
from typing import Protocol, runtime_checkable

from coverai.domain.enums import PaymentStatus
from coverai.domain.payments import PaymentIntent


@runtime_checkable
class PaymentRepo(Protocol):
    async def create(self, intent: PaymentIntent) -> PaymentIntent:
        """Создает платежное намерение."""
        ...

    async def get_by_id(self, payment_id: int) -> PaymentIntent | None:
        """Возвращает платеж по id."""
        ...

    async def get_by_external_id(self, external_id: str) -> PaymentIntent | None:
        """Возвращает платеж по внешнему id."""
        ...

    async def update_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        confirmed_at: datetime | None = None,
    ) -> PaymentIntent | None:
        """Обновляет статус платежа."""
        ...

