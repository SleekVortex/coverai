from enum import StrEnum


class Plan(StrEnum):
    FREE = "free"
    STANDARD = "standard"
    PRO = "pro"


class UserRole(StrEnum):
    USER = "user"
    ADMIN = "admin"


class Tone(StrEnum):
    FORMAL = "formal"
    CONFIDENT = "confident"
    CONCISE = "concise"


class GenerationStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"


class CreditTransactionType(StrEnum):
    WELCOME_BONUS = "welcome_bonus"
    TOP_UP = "top_up"
    PROMO = "promo"
    SPEND = "spend"
    ADJUSTMENT = "adjustment"
    REFUND = "refund"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"
    REFUND_MANUAL_REVIEW = "refund_manual_review"


class PromoCodeType(StrEnum):
    FIXED_CREDITS = "fixed_credits"
    TOP_UP_DISCOUNT = "top_up_discount"
