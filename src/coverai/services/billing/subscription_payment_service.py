from uuid import uuid4

from coverai.domain.entities import User
from coverai.domain.enums import Plan
from coverai.domain.ids import required_id
from coverai.domain.ports import SubscriptionPaymentRepo, SubscriptionRepo
from coverai.domain.read_models import SubscriptionPaymentRead
from coverai.services.billing.errors import InvalidPaidPlanError


class SubscriptionPaymentService:
    def __init__(
        self,
        subscription_repo: SubscriptionRepo,
        subscription_payment_repo: SubscriptionPaymentRepo,
        standard_price_rub: int,
        pro_price_rub: int,
    ) -> None:
        self._subscription_repo = subscription_repo
        self._subscription_payment_repo = subscription_payment_repo
        self._standard_price_rub = standard_price_rub
        self._pro_price_rub = pro_price_rub

    async def create_payment(
        self,
        user: User,
        plan: Plan,
    ) -> SubscriptionPaymentRead | None:
        """Создает платеж подписки или возвращает None для outside MVP downgrade."""
        if plan == Plan.FREE:
            raise InvalidPaidPlanError

        user_id = required_id(user)
        active = await self._subscription_repo.get_active_by_user_id(user_id)
        if active is not None and active.plan == Plan.PRO and plan == Plan.STANDARD:
            return None

        return await self._subscription_payment_repo.create(
            user_id=user_id,
            plan=plan,
            amount_rub=self._price(plan),
            external_id=f"sub_{uuid4().hex}",
        )

    async def active_subscription_payload(
        self,
        user: User,
    ) -> dict[str, object | None]:
        """Возвращает текущую подписку."""
        active = await self._subscription_repo.get_active_by_user_id(required_id(user))
        return {
            "plan": user.plan.value,
            "active_subscription": None
            if active is None
            else {
                "id": active.id,
                "plan": active.plan.value,
                "starts_at": active.starts_at,
                "expires_at": active.expires_at,
            },
        }

    def _price(self, plan: Plan) -> int:
        if plan == Plan.PRO:
            return self._pro_price_rub
        return self._standard_price_rub
