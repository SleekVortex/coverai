from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class CreditTransactionRead:
    id: int
    type: str
    amount: int
    balance_after: int
    description: str
    created_at: datetime


@dataclass(frozen=True, slots=True)
class BillingSummaryRead:
    credits: int
    recent_transactions: list[CreditTransactionRead]


@dataclass(frozen=True, slots=True)
class UserAnalyticsRead:
    total_generations: int
    succeeded_generations: int
    failed_generations: int
    credits_spent: int


@dataclass(frozen=True, slots=True)
class AdminUserSummaryRead:
    id: int
    email: str | None
    telegram_id: int | None
    role: str
    plan: str
    credits: int


@dataclass(frozen=True, slots=True)
class AdminProfileRead:
    id: int
    title: str
    resume_text: str


@dataclass(frozen=True, slots=True)
class AdminSubscriptionRead:
    id: int
    plan: str
    starts_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class AdminUserDetailRead:
    summary: AdminUserSummaryRead
    profile: AdminProfileRead | None
    balance_credits: int
    active_subscription: AdminSubscriptionRead | None
    generation_counts: dict[str, int]


@dataclass(frozen=True, slots=True)
class AdminAnalyticsOverviewRead:
    users_by_plan: dict[str, int]
    generations_per_day: int
    success_rate: float
    revenue: int
    active_subscriptions: int


@dataclass(frozen=True, slots=True)
class SubscriptionPaymentRead:
    id: int
    status: str
    amount_rub: int
    user_id: int
    plan: str
    external_id: str

