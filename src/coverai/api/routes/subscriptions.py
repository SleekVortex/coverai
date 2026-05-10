from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.services import SubscriptionPaymentServiceDep
from coverai.domain.enums import Plan
from coverai.services.billing.errors import InvalidPaidPlanError

router = APIRouter(tags=["subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    plan: Plan


@router.post("/subscriptions")
async def create_subscription_payment(
    payload: SubscriptionCreateRequest,
    user: CurrentUserDep,
    subscription_payment_service: SubscriptionPaymentServiceDep,
) -> dict[str, Any]:
    """Создает платеж подписки."""
    try:
        intent = await subscription_payment_service.create_payment(user, payload.plan)
    except InvalidPaidPlanError as error:
        raise HTTPException(status_code=422, detail="Paid plan required") from error
    if intent is None:
        return {
            "status": "outside_mvp",
            "message": "Downgrade from Pro to Standard is outside MVP",
            "plan": user.plan.value,
        }

    return {
        "id": intent.id,
        "subscription_payment_intent_id": intent.id,
        "payment_intent_id": intent.id,
        "status": intent.status,
        "amount_rub": intent.amount_rub,
        "currency": "RUB",
        "user_id": intent.user_id,
        "plan": intent.plan,
        "external_id": intent.external_id,
    }


@router.get("/subscriptions/current")
async def current_subscription(
    user: CurrentUserDep,
    subscription_payment_service: SubscriptionPaymentServiceDep,
) -> dict[str, Any]:
    """Возвращает текущую подписку."""
    return await subscription_payment_service.active_subscription_payload(user)


@router.post("/subscriptions/current/cancel")
async def cancel_subscription(
    user: CurrentUserDep,
) -> dict[str, Any]:
    """Отменяет подписку."""
    return {
        "status": "outside_mvp",
        "message": "Subscription cancellation is outside MVP",
        "plan": user.plan.value,
    }
