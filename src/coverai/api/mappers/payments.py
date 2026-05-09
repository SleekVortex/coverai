from coverai.api.schemas import PaymentResponse
from coverai.domain.enums import PaymentStatus
from coverai.infra.db import models


def payment_response(intent: models.PaymentIntent) -> PaymentResponse:
    """Преобразует платеж в API response."""
    return PaymentResponse(
        id=intent.id,
        status=PaymentStatus(intent.status),
        credits_amount=intent.credits_amount,
        amount_rub=intent.amount_rub,
        discount_percent=intent.discount_percent,
        external_id=intent.external_id,
        currency="RUB",
        user_id=intent.user_id,
        payment_intent_id=intent.id,
    )
