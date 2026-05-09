from datetime import datetime

from pydantic import BaseModel, Field

from coverai.domain.enums import PromoCodeType


class PromoCreateRequest(BaseModel):
    code: str
    type: PromoCodeType
    value: int = Field(gt=0)
    valid_until: datetime
    max_activations: int = Field(gt=0)
