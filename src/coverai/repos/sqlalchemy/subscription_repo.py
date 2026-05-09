from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain import entities as domain
from coverai.domain.enums import SubscriptionStatus
from coverai.infra.db import models
from coverai.repos.sqlalchemy.mappers import subscription_from_model


class SubscriptionSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, subscription: domain.Subscription) -> domain.Subscription:
        """Создает запись."""
        row = models.Subscription(
            user_id=subscription.user_id,
            plan=subscription.plan.value,
            status=subscription.status.value,
            starts_at=subscription.starts_at,
            expires_at=subscription.expires_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return subscription_from_model(row)

    async def get_active_by_user_id(self, user_id: int) -> domain.Subscription | None:
        """Возвращает активную подписку."""
        statement = (
            select(models.Subscription)
            .where(
                models.Subscription.user_id == user_id,
                models.Subscription.status == SubscriptionStatus.ACTIVE.value,
            )
            .order_by(
                models.Subscription.expires_at.desc(),
                models.Subscription.id.desc(),
            )
        )
        row = await self._session.scalar(statement)
        return subscription_from_model(row) if row else None

    async def update_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
    ) -> domain.Subscription | None:
        """Обновляет статус записи."""
        row = await self._session.get(models.Subscription, subscription_id)
        if row is None:
            return None

        row.status = status.value
        await self._session.flush()
        await self._session.refresh(row)
        return subscription_from_model(row)

    async def list_active_expired_before(
        self,
        now: datetime,
    ) -> list[domain.Subscription]:
        """Возвращает истекшие активные подписки."""
        statement = select(models.Subscription).where(
            models.Subscription.status == SubscriptionStatus.ACTIVE.value,
            models.Subscription.expires_at < now,
        )
        rows = await self._session.scalars(statement)
        return [subscription_from_model(row) for row in rows]
