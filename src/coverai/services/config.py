from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from re import Pattern, compile
from types import MappingProxyType
from zoneinfo import ZoneInfo

from coverai.domain.enums import GenerationStatus, Plan, Tone


@dataclass(frozen=True, slots=True)
class AuthServiceConfig:
    password_algorithm: str = "pbkdf2_sha256"
    password_digest_name: str = "sha256"
    password_hash_iterations: int = 210_000
    password_salt_bytes: int = 16


@dataclass(frozen=True, slots=True)
class PlanLimitConfig:
    limit: int | None
    period: str | None


@dataclass(frozen=True, slots=True)
class BillingServiceConfig:
    paid_subscription_duration: timedelta = timedelta(days=30)
    quota_timezone: ZoneInfo = ZoneInfo("Europe/Moscow")
    quota_statuses: frozenset[GenerationStatus] = frozenset(
        {GenerationStatus.PENDING, GenerationStatus.SUCCEEDED},
    )
    plan_limits: Mapping[Plan, PlanLimitConfig] = field(
        default_factory=lambda: MappingProxyType(
            {
                Plan.FREE: PlanLimitConfig(limit=1, period="day"),
                Plan.STANDARD: PlanLimitConfig(limit=300, period="month"),
                Plan.PRO: PlanLimitConfig(limit=None, period=None),
            },
        ),
    )


@dataclass(frozen=True, slots=True)
class CreditsServiceConfig:
    welcome_bonus_description: str = "Welcome bonus"


@dataclass(frozen=True, slots=True)
class GenerationQueueServiceConfig:
    placeholder_employer_name: str = "Pending hh.ru employer"
    placeholder_vacancy_title: str = "Pending hh.ru vacancy"
    allowed_tones_by_plan: Mapping[Plan, frozenset[Tone]] = field(
        default_factory=lambda: MappingProxyType(
            {
                Plan.FREE: frozenset({Tone.FORMAL}),
                Plan.STANDARD: frozenset(
                    {Tone.FORMAL, Tone.CONFIDENT, Tone.CONCISE},
                ),
                Plan.PRO: frozenset({Tone.FORMAL, Tone.CONFIDENT, Tone.CONCISE}),
            },
        ),
    )


@dataclass(frozen=True, slots=True)
class HistoryServiceConfig:
    standard_history_period: timedelta = timedelta(days=30)
    default_history_limit: int = 20


@dataclass(frozen=True, slots=True)
class ProfileServiceConfig:
    max_profile_title_length: int = 255
    min_resume_text_length: int = 100
    max_resume_text_length: int = 6000


@dataclass(frozen=True, slots=True)
class PromptServiceConfig:
    vacancy_description_max_length: int = 250


@dataclass(frozen=True, slots=True)
class ResumeFileServiceConfig:
    plain_text_encoding: str = "utf-8"
    plain_text_suffixes: frozenset[str] = frozenset({".txt", ".md"})
    docx_suffix: str = ".docx"
    pdf_suffix: str = ".pdf"


@dataclass(frozen=True, slots=True)
class VacancyServiceConfig:
    cache_ttl: timedelta = timedelta(hours=1)
    hh_url_pattern: Pattern[str] = compile(r"https?://[^\s<>()]+")
    hh_root_host: str = "hh.ru"
    open_type_id: str = "open"
    truthy_text: str = "true"


@dataclass(frozen=True, slots=True)
class ServiceConfig:
    auth: AuthServiceConfig = AuthServiceConfig()
    billing: BillingServiceConfig = BillingServiceConfig()
    credits: CreditsServiceConfig = CreditsServiceConfig()
    generation_queue: GenerationQueueServiceConfig = GenerationQueueServiceConfig()
    history: HistoryServiceConfig = HistoryServiceConfig()
    profile: ProfileServiceConfig = ProfileServiceConfig()
    prompts: PromptServiceConfig = PromptServiceConfig()
    resume_files: ResumeFileServiceConfig = ResumeFileServiceConfig()
    vacancy: VacancyServiceConfig = VacancyServiceConfig()


SERVICE_CONFIG = ServiceConfig()

