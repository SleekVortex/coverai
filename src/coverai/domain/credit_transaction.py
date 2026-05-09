from dataclasses import dataclass
from datetime import datetime

from coverai.domain.enums import CreditTransactionType


@dataclass(frozen=True, slots=True)
class CreditTransaction:
    user_id: int
    type: CreditTransactionType
    amount: int
    balance_after: int
    description: str
    id: int | None = None
    generation_request_id: int | None = None
    payment_intent_id: int | None = None
    promo_code_id: int | None = None
    metadata_json: dict[str, object] | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
