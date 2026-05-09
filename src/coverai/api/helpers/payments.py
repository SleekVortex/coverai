from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.infra.db import models


async def payment_by_external_id(
    session: AsyncSession,
    external_id: str,
) -> models.PaymentIntent | None:
    """Возвращает платеж по внешнему id."""
    return await session.scalar(
        select(models.PaymentIntent).where(
            models.PaymentIntent.external_id == external_id,
        ),
    )
