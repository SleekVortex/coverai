from dataclasses import dataclass
from datetime import datetime

from coverai.domain.enums import PaymentStatus


@dataclass(frozen=True, slots=True)
class PaymentIntent:
    user_id: int
    credits_amount: int
    amount_rub: int
    discount_percent: int
    status: PaymentStatus
    provider: str
    external_id: str
    id: int | None = None
    confirmed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

