from coverai.api.schemas import PaymentResponse
from coverai.domain.enums import PaymentStatus
from coverai.domain.ids import required_id
from coverai.domain.payments import PaymentIntent


def payment_response(intent: PaymentIntent) -> PaymentResponse:
    """Преобразует платеж в API response."""
    payment_id = required_id(intent)
    return PaymentResponse(
        id=payment_id,
        status=PaymentStatus(intent.status),
        credits_amount=intent.credits_amount,
        amount_rub=intent.amount_rub,
        discount_percent=intent.discount_percent,
        external_id=intent.external_id,
        currency="RUB",
        user_id=intent.user_id,
        payment_intent_id=payment_id,
    )
