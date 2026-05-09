from pydantic import BaseModel


class PromoRedeemRequest(BaseModel):
    code: str
