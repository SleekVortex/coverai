from datetime import UTC, datetime

from coverai.domain.entities import Subscription
from coverai.domain.enums import Plan, SubscriptionStatus
from coverai.domain.ports import SubscriptionRepo, UserRepo
from coverai.services.billing.errors import InvalidPaidPlanError
from coverai.services.config import SERVICE_CONFIG
from coverai.services.users.errors import UserNotFoundError

PAID_SUBSCRIPTION_DURATION = SERVICE_CONFIG.billing.paid_subscription_duration


class BillingService:
    def __init__(
        self,
        user_repo: UserRepo,
        subscription_repo: SubscriptionRepo,
    ) -> None:
        self._user_repo = user_repo
        self._subscription_repo = subscription_repo

    async def activate_subscription(
        self,
        user_id: int,
        plan: Plan,
        now: datetime | None = None,
    ) -> Subscription:
        """Активирует подписку."""
        if plan not in {Plan.STANDARD, Plan.PRO}:
            raise InvalidPaidPlanError

        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        activated_at = now or datetime.now(UTC)
        current = await self._subscription_repo.get_active_by_user_id(user_id)
        if current is not None and current.plan == plan:
            activated_at = current.expires_at
        elif current is not None and current.id is not None:
            await self._subscription_repo.update_status(
                current.id,
                SubscriptionStatus.EXPIRED,
            )

        subscription = await self._subscription_repo.create(
            Subscription(
                user_id=user_id,
                plan=plan,
                status=SubscriptionStatus.ACTIVE,
                starts_at=activated_at,
                expires_at=activated_at + PAID_SUBSCRIPTION_DURATION,
            ),
        )
        await self._user_repo.update_plan(user_id, plan)
        return subscription

    async def expire_subscriptions(
        self,
        now: datetime | None = None,
    ) -> list[Subscription]:
        """Завершает истекшие подписки."""
        cutoff = now or datetime.now(UTC)
        expired = await self._subscription_repo.list_active_expired_before(cutoff)

        for subscription in expired:
            if subscription.id is None:
                continue

            await self._subscription_repo.update_status(
                subscription.id,
                SubscriptionStatus.EXPIRED,
            )
            await self._user_repo.update_plan(subscription.user_id, Plan.FREE)

        return expired
