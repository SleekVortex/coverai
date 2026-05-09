from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.domain.enums import PaymentStatus, Plan
from coverai.infra.db import models

router = APIRouter(tags=["subscriptions"])


class SubscriptionCreateRequest(BaseModel):
    plan: Plan


@router.post("/subscriptions")
async def create_subscription_payment(
    payload: SubscriptionCreateRequest,
    user: CurrentUserDep,
    session: SessionDep,
    request: Request,
) -> dict[str, Any]:
    """Создает платеж подписки."""
    if payload.plan == Plan.FREE:
        raise HTTPException(status_code=422, detail="Paid plan required")

    active = await _active_subscription(session, user.id)
    if (
        active is not None
        and active.plan == Plan.PRO.value
        and payload.plan == Plan.STANDARD
    ):
        return {
            "status": "outside_mvp",
            "message": "Downgrade from Pro to Standard is outside MVP",
            "plan": user.plan,
        }

    amount = _subscription_price(request, payload.plan)
    intent = models.SubscriptionPaymentIntent(
        user_id=user.id,
        plan=payload.plan.value,
        amount_rub=amount,
        status=PaymentStatus.PENDING.value,
        provider="mock",
        external_id=f"sub_{uuid4().hex}",
    )
    session.add(intent)
    await session.flush()
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
    session: SessionDep,
) -> dict[str, Any]:
    """Возвращает текущую подписку."""
    active = await _active_subscription(session, user.id)
    return {
        "plan": user.plan,
        "active_subscription": None
        if active is None
        else {
            "id": active.id,
            "plan": active.plan,
            "starts_at": active.starts_at,
            "expires_at": active.expires_at,
        },
    }


@router.post("/subscriptions/current/cancel")
async def cancel_subscription(
    user: CurrentUserDep,
) -> dict[str, Any]:
    """Отменяет подписку."""
    return {
        "status": "outside_mvp",
        "message": "Subscription cancellation is outside MVP",
        "plan": user.plan,
    }


async def _active_subscription(
    session: SessionDep,
    user_id: int,
) -> models.Subscription | None:
    return await session.scalar(
        select(models.Subscription)
        .where(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "active",
        )
        .order_by(models.Subscription.expires_at.desc()),
    )


def _subscription_price(request: Request, plan: Plan) -> int:
    if plan == Plan.PRO:
        return request.app.state.settings.billing.pro_subscription_price_rub
    return request.app.state.settings.billing.standard_subscription_price_rub
