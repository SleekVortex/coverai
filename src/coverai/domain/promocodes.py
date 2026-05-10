from dataclasses import dataclass
from datetime import datetime

from coverai.domain.enums import PromoCodeType


@dataclass(frozen=True, slots=True)
class PromoCode:
    code: str
    type: PromoCodeType
    value: int
    valid_until: datetime
    max_activations: int
    activations_count: int = 0
    is_active: bool = True
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

