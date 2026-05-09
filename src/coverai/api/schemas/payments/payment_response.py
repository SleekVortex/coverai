from pydantic import BaseModel

from coverai.domain.enums import PaymentStatus


class PaymentResponse(BaseModel):
    id: int
    status: PaymentStatus
    credits_amount: int
    amount_rub: int
    discount_percent: int
    external_id: str
    currency: str
    user_id: int
    payment_intent_id: int
