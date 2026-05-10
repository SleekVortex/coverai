from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.enums import CreditTransactionType, GenerationStatus, Plan
from coverai.domain.read_models import (
    AdminAnalyticsOverviewRead,
    AdminProfileRead,
    AdminSubscriptionRead,
    AdminUserDetailRead,
    AdminUserSummaryRead,
    BillingSummaryRead,
    CreditTransactionRead,
    UserAnalyticsRead,
)
from coverai.infra.db import models


class BillingReadSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def billing_summary(
        self,
        user_id: int,
        recent_limit: int = 5,
    ) -> BillingSummaryRead:
        """Возвращает баланс и последние транзакции."""
        user = await self._session.get(models.User, user_id)
        credits = int(user.credits) if user is not None else 0
        rows = await self._transaction_rows(user_id, recent_limit)
        return BillingSummaryRead(
            credits=credits,
            recent_transactions=[_transaction_read(row) for row in rows],
        )

    async def transactions(self, user_id: int) -> list[CreditTransactionRead]:
        """Возвращает транзакции пользователя."""
        rows = await self._transaction_rows(user_id, None)
        return [_transaction_read(row) for row in rows]

    async def _transaction_rows(
        self,
        user_id: int,
        limit: int | None,
    ) -> list[models.CreditTransaction]:
        statement = (
            select(models.CreditTransaction)
            .where(models.CreditTransaction.user_id == user_id)
            .order_by(models.CreditTransaction.created_at.desc())
        )
        if limit is not None:
            statement = statement.limit(limit)
        return list(await self._session.scalars(statement))


class AnalyticsReadSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def user_usage(self, user_id: int) -> UserAnalyticsRead:
        """Возвращает пользовательскую аналитику."""
        total = await self._session.scalar(
            select(func.count())
            .select_from(models.GenerationRequest)
            .where(models.GenerationRequest.user_id == user_id),
        )
        succeeded = await self._session.scalar(
            select(func.count())
            .select_from(models.GenerationRequest)
            .where(
                models.GenerationRequest.user_id == user_id,
                models.GenerationRequest.status == GenerationStatus.SUCCEEDED.value,
            ),
        )
        failed = await self._session.scalar(
            select(func.count())
            .select_from(models.GenerationRequest)
            .where(
                models.GenerationRequest.user_id == user_id,
                models.GenerationRequest.status == GenerationStatus.FAILED.value,
            ),
        )
        spent = await self._session.scalar(
            select(func.coalesce(func.sum(models.CreditTransaction.amount), 0)).where(
                models.CreditTransaction.user_id == user_id,
                models.CreditTransaction.type == CreditTransactionType.SPEND.value,
            ),
        )
        return UserAnalyticsRead(
            total_generations=int(total or 0),
            succeeded_generations=int(succeeded or 0),
            failed_generations=int(failed or 0),
            credits_spent=abs(int(spent or 0)),
        )


class AdminReadSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_users(
        self,
        limit: int,
        offset: int,
        plan: Plan | None,
        role: str | None,
    ) -> list[AdminUserSummaryRead]:
        """Возвращает пользователей для админки."""
        statement = select(models.User)
        if plan is not None:
            statement = statement.where(models.User.plan == plan.value)
        if role is not None:
            statement = statement.where(models.User.role == role)
        rows = await self._session.scalars(statement.offset(offset).limit(limit))
        return [_user_summary(row) for row in rows]

    async def user_detail(self, user_id: int) -> AdminUserDetailRead | None:
        """Возвращает детали пользователя для админки."""
        target = await self._session.get(models.User, user_id)
        if target is None:
            return None

        profile = await self._session.scalar(
            select(models.ResumeProfile).where(
                models.ResumeProfile.user_id == user_id,
            ),
        )
        active_subscription = await self._active_subscription(user_id)
        return AdminUserDetailRead(
            summary=_user_summary(target),
            profile=None
            if profile is None
            else AdminProfileRead(
                id=profile.id,
                title=profile.title,
                resume_text=profile.resume_text,
            ),
            balance_credits=target.credits,
            active_subscription=_subscription_read(active_subscription),
            generation_counts=await self._generation_counts(user_id),
        )

    async def analytics_overview(self) -> AdminAnalyticsOverviewRead:
        """Возвращает административную аналитику."""
        users_by_plan = {
            plan.value: int(
                await self._session.scalar(
                    select(func.count())
                    .select_from(models.User)
                    .where(models.User.plan == plan.value),
                )
                or 0,
            )
            for plan in Plan
        }
        total_generations = int(
            await self._session.scalar(
                select(func.count()).select_from(models.GenerationRequest),
            )
            or 0,
        )
        succeeded_generations = int(
            await self._session.scalar(
                select(func.count())
                .select_from(models.GenerationRequest)
                .where(
                    models.GenerationRequest.status
                    == GenerationStatus.SUCCEEDED.value,
                ),
            )
            or 0,
        )
        revenue = int(
            await self._session.scalar(
                select(func.coalesce(func.sum(models.PaymentIntent.amount_rub), 0))
                .where(models.PaymentIntent.status == "succeeded"),
            )
            or 0,
        )
        active_subscriptions = int(
            await self._session.scalar(
                select(func.count())
                .select_from(models.Subscription)
                .where(models.Subscription.status == "active"),
            )
            or 0,
        )
        return AdminAnalyticsOverviewRead(
            users_by_plan=users_by_plan,
            generations_per_day=total_generations,
            success_rate=0
            if total_generations == 0
            else succeeded_generations / total_generations,
            revenue=revenue,
            active_subscriptions=active_subscriptions,
        )

    async def _active_subscription(
        self,
        user_id: int,
    ) -> models.Subscription | None:
        return await self._session.scalar(
            select(models.Subscription)
            .where(
                models.Subscription.user_id == user_id,
                models.Subscription.status == "active",
            )
            .order_by(models.Subscription.expires_at.desc()),
        )

    async def _generation_counts(self, user_id: int) -> dict[str, int]:
        counts: dict[str, int] = {}
        for status in GenerationStatus:
            counts[status.value] = int(
                await self._session.scalar(
                    select(func.count())
                    .select_from(models.GenerationRequest)
                    .where(
                        models.GenerationRequest.user_id == user_id,
                        models.GenerationRequest.status == status.value,
                    ),
                )
                or 0,
            )
        return counts


def _transaction_read(row: models.CreditTransaction) -> CreditTransactionRead:
    return CreditTransactionRead(
        id=row.id,
        type=row.type,
        amount=row.amount,
        balance_after=row.balance_after,
        description=row.description,
        created_at=row.created_at,
    )


def _user_summary(row: models.User) -> AdminUserSummaryRead:
    return AdminUserSummaryRead(
        id=row.id,
        email=row.email,
        telegram_id=row.telegram_id,
        role=row.role,
        plan=row.plan,
        credits=row.credits,
    )


def _subscription_read(
    row: models.Subscription | None,
) -> AdminSubscriptionRead | None:
    if row is None:
        return None
    return AdminSubscriptionRead(
        id=row.id,
        plan=row.plan,
        starts_at=row.starts_at,
        expires_at=row.expires_at,
    )

