from pydantic import BaseModel

from coverai.domain.enums import PromoCodeType


class PromoResponse(BaseModel):
    code: str
    type: PromoCodeType
    value: int
    message: str
