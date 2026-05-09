from pydantic import BaseModel, Field


class PaymentCreateRequest(BaseModel):
    credits_amount: int = Field(gt=0)
