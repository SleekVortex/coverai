from datetime import datetime

from pydantic import BaseModel


class RecentCreditTransactionResponse(BaseModel):
    id: int
    type: str
    amount: int
    balance_after: int
    description: str
    created_at: datetime


class PlanUsageResponse(BaseModel):
    plan: str
    used: int
    limit: int | None
    remaining: int | None
    period: str | None
    credits: int
    generation_cost_credits: int
    recent_transactions: list[RecentCreditTransactionResponse]
