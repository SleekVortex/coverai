from fastapi import APIRouter, HTTPException

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.services import PaymentServiceDep
from coverai.api.mappers.payments import payment_response
from coverai.api.schemas import PaymentCreateRequest, PaymentResponse
from coverai.services.billing.errors import (
    PaymentNotFoundError,
    PaymentNotRefundableError,
)

router = APIRouter(tags=["payments"])


@router.post("/payments", response_model=PaymentResponse)
async def create_payment(
    payload: PaymentCreateRequest,
    user: CurrentUserDep,
    payment_service: PaymentServiceDep,
) -> PaymentResponse:
    """Создает платеж."""
    intent = await payment_service.create_top_up(
        user=user,
        credits_amount=payload.credits_amount,
    )
    return payment_response(intent)


@router.post(
    "/webhooks/mock-payment/{external_id}",
    response_model=PaymentResponse,
)
async def confirm_payment(
    external_id: str,
    payment_service: PaymentServiceDep,
) -> PaymentResponse:
    """Подтверждает платеж."""
    try:
        intent = await payment_service.confirm(external_id)
    except PaymentNotFoundError as error:
        raise HTTPException(status_code=404, detail="Payment not found") from error
    return payment_response(intent)


@router.post(
    "/webhooks/mock-payment/{external_id}/fail",
    response_model=PaymentResponse,
)
async def fail_payment(
    external_id: str,
    payment_service: PaymentServiceDep,
) -> PaymentResponse:
    """Помечает платеж ошибочным."""
    try:
        intent = await payment_service.fail(external_id)
    except PaymentNotFoundError as error:
        raise HTTPException(status_code=404, detail="Payment not found") from error
    return payment_response(intent)


@router.post(
    "/webhooks/mock-payment/{external_id}/cancel",
    response_model=PaymentResponse,
)
async def cancel_payment(
    external_id: str,
    payment_service: PaymentServiceDep,
) -> PaymentResponse:
    """Отменяет платеж."""
    try:
        intent = await payment_service.cancel(external_id)
    except PaymentNotFoundError as error:
        raise HTTPException(status_code=404, detail="Payment not found") from error
    return payment_response(intent)


@router.post("/payments/{payment_id}/refund", response_model=PaymentResponse)
async def refund_payment(
    payment_id: int,
    payment_service: PaymentServiceDep,
) -> PaymentResponse:
    """Возвращает платеж."""
    try:
        intent = await payment_service.refund(payment_id)
    except PaymentNotFoundError as error:
        raise HTTPException(status_code=404, detail="Payment not found") from error
    except PaymentNotRefundableError as error:
        raise HTTPException(
            status_code=409,
            detail="Payment is not refundable",
        ) from error
    return payment_response(intent)
