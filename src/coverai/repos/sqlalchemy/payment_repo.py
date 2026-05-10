from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.enums import PaymentStatus
from coverai.domain.payments import PaymentIntent
from coverai.infra.db import models


class PaymentSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, intent: PaymentIntent) -> PaymentIntent:
        """Создает платежное намерение."""
        row = models.PaymentIntent(
            user_id=intent.user_id,
            credits_amount=intent.credits_amount,
            amount_rub=intent.amount_rub,
            discount_percent=intent.discount_percent,
            status=intent.status.value,
            provider=intent.provider,
            external_id=intent.external_id,
            confirmed_at=intent.confirmed_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return payment_from_model(row)

    async def get_by_id(self, payment_id: int) -> PaymentIntent | None:
        """Возвращает платеж по id."""
        row = await self._session.get(
            models.PaymentIntent,
            payment_id,
            with_for_update=True,
        )
        return payment_from_model(row) if row else None

    async def get_by_external_id(self, external_id: str) -> PaymentIntent | None:
        """Возвращает платеж по внешнему id."""
        row = await self._session.scalar(
            select(models.PaymentIntent)
            .where(models.PaymentIntent.external_id == external_id)
            .with_for_update(),
        )
        return payment_from_model(row) if row else None

    async def update_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        confirmed_at: datetime | None = None,
    ) -> PaymentIntent | None:
        """Обновляет статус платежа."""
        row = await self._session.get(models.PaymentIntent, payment_id)
        if row is None:
            return None

        row.status = status.value
        row.confirmed_at = confirmed_at
        await self._session.flush()
        await self._session.refresh(row)
        return payment_from_model(row)


def payment_from_model(row: models.PaymentIntent) -> PaymentIntent:
    """Преобразует модель платежа."""
    return PaymentIntent(
        id=row.id,
        user_id=row.user_id,
        credits_amount=row.credits_amount,
        amount_rub=row.amount_rub,
        discount_percent=row.discount_percent,
        status=PaymentStatus(row.status),
        provider=row.provider,
        external_id=row.external_id,
        confirmed_at=row.confirmed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
