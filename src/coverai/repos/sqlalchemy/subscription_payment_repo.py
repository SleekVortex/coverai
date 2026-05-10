from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.enums import PaymentStatus, Plan
from coverai.domain.read_models import SubscriptionPaymentRead
from coverai.infra.db import models


class SubscriptionPaymentSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: int,
        plan: Plan,
        amount_rub: int,
        external_id: str,
    ) -> SubscriptionPaymentRead:
        """Создает платежное намерение подписки."""
        row = models.SubscriptionPaymentIntent(
            user_id=user_id,
            plan=plan.value,
            amount_rub=amount_rub,
            status=PaymentStatus.PENDING.value,
            provider="mock",
            external_id=external_id,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return SubscriptionPaymentRead(
            id=row.id,
            status=row.status,
            amount_rub=row.amount_rub,
            user_id=row.user_id,
            plan=row.plan,
            external_id=row.external_id,
        )

