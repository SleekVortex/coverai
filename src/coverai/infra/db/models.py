from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from coverai.domain.enums import (
    CreditTransactionType,
    GenerationStatus,
    PaymentStatus,
    Plan,
    PromoCodeType,
    SubscriptionStatus,
    Tone,
    UserRole,
)
from coverai.infra.db.base import Base

PLAN_VALUES = tuple(plan.value for plan in Plan)
USER_ROLE_VALUES = tuple(role.value for role in UserRole)
TONE_VALUES = tuple(tone.value for tone in Tone)
GENERATION_STATUS_VALUES = tuple(status.value for status in GenerationStatus)
SUBSCRIPTION_STATUS_VALUES = tuple(status.value for status in SubscriptionStatus)
CREDIT_TRANSACTION_TYPE_VALUES = tuple(item.value for item in CreditTransactionType)
PAYMENT_STATUS_VALUES = tuple(status.value for status in PaymentStatus)
PROMO_CODE_TYPE_VALUES = tuple(kind.value for kind in PromoCodeType)


def enum_check(column_name: str, values: tuple[str, ...]) -> str:
    """Создает SQL check для enum."""
    quoted_values = ", ".join(f"'{value}'" for value in values)
    return f"{column_name} IN ({quoted_values})"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(enum_check("plan", PLAN_VALUES), name="plan"),
        CheckConstraint(enum_check("role", USER_ROLE_VALUES), name="role"),
        CheckConstraint("credits >= 0", name="credits_non_negative"),
        CheckConstraint(
            "pending_top_up_discount_percent >= 0 "
            "AND pending_top_up_discount_percent <= 100",
            name="pending_top_up_discount_percent_range",
        ),
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("telegram_id", name="uq_users_telegram_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int | None] = mapped_column(BigInteger)
    email: Mapped[str | None] = mapped_column(String(320))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{UserRole.USER.value}'"),
    )
    credits: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    pending_top_up_discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    pending_top_up_discount_valid_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    pending_top_up_discount_promo_code_id: Mapped[int | None] = mapped_column(
        ForeignKey("promo_codes.id"),
    )
    plan: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{Plan.FREE.value}'"),
    )
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    language_code: Mapped[str | None] = mapped_column(String(16))


class ResumeProfile(TimestampMixin, Base):
    __tablename__ = "resume_profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_resume_profiles_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        server_default=text("'Resume'"),
    )
    resume_text: Mapped[str] = mapped_column(Text, nullable=False)


class Employer(TimestampMixin, Base):
    __tablename__ = "employers"
    __table_args__ = (UniqueConstraint("hh_id", name="uq_employers_hh_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hh_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON)
    cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Vacancy(TimestampMixin, Base):
    __tablename__ = "vacancies"
    __table_args__ = (UniqueConstraint("hh_id", name="uq_vacancies_hh_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    hh_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    employer_id: Mapped[int] = mapped_column(
        ForeignKey("employers.id"),
        nullable=False,
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    url: Mapped[str | None] = mapped_column(String(2048))
    raw_payload: Mapped[dict[str, object] | None] = mapped_column(JSON)
    cached_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class GenerationRequest(TimestampMixin, Base):
    __tablename__ = "generation_requests"
    __table_args__ = (
        CheckConstraint(
            enum_check("status", GENERATION_STATUS_VALUES),
            name="status",
        ),
        CheckConstraint(
            enum_check("tone", TONE_VALUES),
            name="tone",
        ),
        Index(
            "ix_generation_requests_user_id_status_created_at",
            "user_id",
            "status",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("resume_profiles.id"),
        nullable=False,
    )
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{GenerationStatus.PENDING.value}'"),
    )
    tone: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    snapshot_profile_text: Mapped[str | None] = mapped_column(Text)
    snapshot_vacancy_text: Mapped[str | None] = mapped_column(Text)
    snapshot_tone: Mapped[str | None] = mapped_column(String(20))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CoverLetter(Base):
    __tablename__ = "cover_letters"
    __table_args__ = (
        CheckConstraint(enum_check("tone", TONE_VALUES), name="tone"),
        Index("ix_cover_letters_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    generation_request_id: Mapped[int] = mapped_column(
        ForeignKey("generation_requests.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    profile_id: Mapped[int] = mapped_column(
        ForeignKey("resume_profiles.id"),
        nullable=False,
    )
    vacancy_id: Mapped[int] = mapped_column(ForeignKey("vacancies.id"), nullable=False)
    employer_id: Mapped[int] = mapped_column(ForeignKey("employers.id"), nullable=False)
    vacancy_title: Mapped[str] = mapped_column(String(512), nullable=False)
    employer_name: Mapped[str] = mapped_column(String(512), nullable=False)
    tone: Mapped[str] = mapped_column(String(20), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_context: Mapped[str] = mapped_column(Text, nullable=False)
    model: Mapped[str] = mapped_column(String(255), nullable=False)
    generation_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class Subscription(TimestampMixin, Base):
    __tablename__ = "subscriptions"
    __table_args__ = (
        CheckConstraint(enum_check("plan", PLAN_VALUES), name="plan"),
        CheckConstraint(
            enum_check("status", SUBSCRIPTION_STATUS_VALUES),
            name="status",
        ),
        Index(
            "ix_subscriptions_user_id_status_expires_at",
            "user_id",
            "status",
            "expires_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{SubscriptionStatus.ACTIVE.value}'"),
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )


class CreditTransaction(TimestampMixin, Base):
    __tablename__ = "credit_transactions"
    __table_args__ = (
        CheckConstraint(
            enum_check("type", CREDIT_TRANSACTION_TYPE_VALUES),
            name="type",
        ),
        Index(
            "ix_credit_transactions_user_id_created_at",
            "user_id",
            "created_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    balance_after: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(512), nullable=False)
    generation_request_id: Mapped[int | None] = mapped_column(
        ForeignKey("generation_requests.id"),
    )
    payment_intent_id: Mapped[int | None] = mapped_column(
        ForeignKey("payment_intents.id"),
    )
    promo_code_id: Mapped[int | None] = mapped_column(ForeignKey("promo_codes.id"))
    metadata_json: Mapped[dict[str, object] | None] = mapped_column(JSON)


class PaymentIntent(TimestampMixin, Base):
    __tablename__ = "payment_intents"
    __table_args__ = (
        CheckConstraint(enum_check("status", PAYMENT_STATUS_VALUES), name="status"),
        CheckConstraint("credits_amount > 0", name="credits_amount_positive"),
        CheckConstraint("amount_rub >= 0", name="amount_rub_non_negative"),
        Index("ix_payment_intents_user_id_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    credits_amount: Mapped[int] = mapped_column(Integer, nullable=False)
    amount_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    discount_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{PaymentStatus.PENDING.value}'"),
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class SubscriptionPaymentIntent(TimestampMixin, Base):
    __tablename__ = "subscription_payment_intents"
    __table_args__ = (
        CheckConstraint(enum_check("plan", PLAN_VALUES), name="plan"),
        CheckConstraint(enum_check("status", PAYMENT_STATUS_VALUES), name="status"),
        CheckConstraint("amount_rub >= 0", name="subscription_amount_rub_non_negative"),
        Index(
            "ix_subscription_payment_intents_user_id_status",
            "user_id",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    plan: Mapped[str] = mapped_column(String(20), nullable=False)
    amount_rub: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text(f"'{PaymentStatus.PENDING.value}'"),
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)
    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PromoCode(TimestampMixin, Base):
    __tablename__ = "promo_codes"
    __table_args__ = (
        CheckConstraint(enum_check("type", PROMO_CODE_TYPE_VALUES), name="type"),
        CheckConstraint("value > 0", name="value_positive"),
        CheckConstraint("max_activations > 0", name="max_activations_positive"),
        CheckConstraint("activations_count >= 0", name="activations_count_positive"),
        UniqueConstraint("code", name="uq_promo_codes_code"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)
    valid_until: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    max_activations: Mapped[int] = mapped_column(Integer, nullable=False)
    activations_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("1"),
    )


class PromoRedemption(TimestampMixin, Base):
    __tablename__ = "promo_redemptions"
    __table_args__ = (
        UniqueConstraint(
            "promo_code_id",
            "user_id",
            name="uq_promo_redemptions_code_user",
        ),
        Index("ix_promo_redemptions_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    promo_code_id: Mapped[int] = mapped_column(
        ForeignKey("promo_codes.id"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
