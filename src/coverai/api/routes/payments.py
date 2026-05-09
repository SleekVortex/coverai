from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.api.helpers.payments import payment_by_external_id
from coverai.api.helpers.users import locked_user
from coverai.api.mappers.payments import payment_response
from coverai.api.schemas import PaymentCreateRequest, PaymentResponse
from coverai.domain.enums import CreditTransactionType, PaymentStatus
from coverai.infra.db import models

router = APIRouter(tags=["payments"])


@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    payload: PaymentCreateRequest,
    user: CurrentUserDep,
    session: SessionDep,
    request: Request,
) -> PaymentResponse:
    """Создает платеж."""
    now = datetime.now(UTC)
    discount = user.pending_top_up_discount_percent
    if _discount_expired(user.pending_top_up_discount_valid_until, now):
        user.pending_top_up_discount_percent = 0
        user.pending_top_up_discount_valid_until = None
        user.pending_top_up_discount_promo_code_id = None
        discount = 0
    credit_price_rub = request.app.state.settings.billing.credit_price_rub
    amount = payload.credits_amount * credit_price_rub
    discounted_amount = amount * (100 - discount) // 100
    intent = models.PaymentIntent(
        user_id=user.id,
        credits_amount=payload.credits_amount,
        amount_rub=discounted_amount,
        discount_percent=discount,
        status=PaymentStatus.PENDING.value,
        provider="mock",
        external_id=f"mock_{uuid4().hex}",
    )
    session.add(intent)
    await session.flush()
    return payment_response(intent)


def _discount_expired(valid_until: datetime | None, now: datetime) -> bool:
    if valid_until is None:
        return False
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=UTC)
    return valid_until <= now


@router.post(
    "/webhooks/mock-payment/{external_id}",
    response_model=PaymentResponse,
)
async def confirm_payment(
    external_id: str,
    session: SessionDep,
) -> PaymentResponse:
    """Подтверждает платеж."""
    intent = await payment_by_external_id(session, external_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if intent.status == PaymentStatus.SUCCEEDED.value:
        return payment_response(intent)

    user = await locked_user(session, intent.user_id)
    user.credits += intent.credits_amount
    user.pending_top_up_discount_percent = 0
    user.pending_top_up_discount_valid_until = None
    user.pending_top_up_discount_promo_code_id = None
    intent.status = PaymentStatus.SUCCEEDED.value
    intent.confirmed_at = datetime.now(UTC)
    session.add(
        models.CreditTransaction(
            user_id=user.id,
            type=CreditTransactionType.TOP_UP.value,
            amount=intent.credits_amount,
            balance_after=user.credits,
            description="Mock payment top-up",
            payment_intent_id=intent.id,
        ),
    )
    await session.flush()
    return payment_response(intent)


@router.post(
    "/webhooks/mock-payment/{external_id}/fail",
    response_model=PaymentResponse,
)
async def fail_payment(
    external_id: str,
    session: SessionDep,
) -> PaymentResponse:
    """Помечает платеж ошибочным."""
    intent = await payment_by_external_id(session, external_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if intent.status == PaymentStatus.PENDING.value:
        intent.status = PaymentStatus.FAILED.value
        intent.confirmed_at = datetime.now(UTC)
        await session.flush()
    return payment_response(intent)


@router.post(
    "/webhooks/mock-payment/{external_id}/cancel",
    response_model=PaymentResponse,
)
async def cancel_payment(
    external_id: str,
    session: SessionDep,
) -> PaymentResponse:
    """Отменяет платеж."""
    intent = await payment_by_external_id(session, external_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if intent.status == PaymentStatus.PENDING.value:
        intent.status = PaymentStatus.CANCELED.value
        intent.confirmed_at = datetime.now(UTC)
        await session.flush()
    return payment_response(intent)


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: int,
    session: SessionDep,
) -> PaymentResponse:
    """Возвращает платеж."""
    intent = await session.get(models.PaymentIntent, payment_id)
    if intent is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if intent.status not in {
        PaymentStatus.SUCCEEDED.value,
        PaymentStatus.REFUNDED.value,
        PaymentStatus.REFUND_MANUAL_REVIEW.value,
    }:
        raise HTTPException(status_code=409, detail="Payment is not refundable")
    if intent.status != PaymentStatus.SUCCEEDED.value:
        return payment_response(intent)

    locked = await locked_user(session, intent.user_id)
    if locked.credits < intent.credits_amount:
        intent.status = PaymentStatus.REFUND_MANUAL_REVIEW.value
        await session.flush()
        return payment_response(intent)

    locked.credits -= intent.credits_amount
    intent.status = PaymentStatus.REFUNDED.value
    intent.confirmed_at = datetime.now(UTC)
    session.add(
        models.CreditTransaction(
            user_id=locked.id,
            type=CreditTransactionType.REFUND.value,
            amount=-intent.credits_amount,
            balance_after=locked.credits,
            description="Mock payment refund",
            payment_intent_id=intent.id,
        ),
    )
    await session.flush()
    return payment_response(intent)
