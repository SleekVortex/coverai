from dataclasses import dataclass
from datetime import datetime

from coverai.domain.enums import (
    GenerationStatus,
    Plan,
    SubscriptionStatus,
    Tone,
    UserRole,
)


@dataclass(frozen=True, slots=True)
class User:
    telegram_id: int | None
    plan: Plan = Plan.FREE
    id: int | None = None
    email: str | None = None
    password_hash: str | None = None
    role: UserRole = UserRole.USER
    credits: int = 0
    pending_top_up_discount_percent: int = 0
    pending_top_up_discount_valid_until: datetime | None = None
    pending_top_up_discount_promo_code_id: int | None = None
    username: str | None = None
    first_name: str | None = None
    language_code: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class ResumeProfile:
    user_id: int
    resume_text: str
    title: str = "Resume"
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Employer:
    hh_id: int
    name: str
    id: int | None = None
    url: str | None = None
    raw_payload: dict[str, object] | None = None
    cached_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Vacancy:
    hh_id: int
    employer_id: int
    title: str
    id: int | None = None
    url: str | None = None
    raw_payload: dict[str, object] | None = None
    cached_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GenerationRequest:
    user_id: int
    profile_id: int
    vacancy_id: int
    status: GenerationStatus
    tone: Tone
    id: int | None = None
    error_message: str | None = None
    snapshot_profile_text: str | None = None
    snapshot_vacancy_text: str | None = None
    snapshot_tone: Tone | None = None
    completed_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CoverLetter:
    generation_request_id: int
    user_id: int
    profile_id: int
    vacancy_id: int
    employer_id: int
    vacancy_title: str
    employer_name: str
    tone: Tone
    text: str
    prompt_context: str
    model: str
    generation_ms: int
    id: int | None = None
    created_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Subscription:
    user_id: int
    plan: Plan
    status: SubscriptionStatus
    starts_at: datetime
    expires_at: datetime
    id: int | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
