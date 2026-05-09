from prometheus_client import Counter, Gauge, Histogram

from coverai.domain.enums import GenerationStatus, Plan

GENERATION_REQUESTS_TOTAL = Counter(
    "coverai_generation_requests_total",
    "Cover letter generation requests by final status and plan.",
    labelnames=("status", "plan"),
)
GENERATION_LATENCY_SECONDS = Histogram(
    "coverai_generation_latency_seconds",
    "End-to-end cover letter generation latency.",
)
HH_LATENCY_SECONDS = Histogram(
    "coverai_hh_latency_seconds",
    "hh.ru vacancy loading latency.",
)
QUOTA_USAGE = Gauge(
    "coverai_quota_usage",
    "Current quota usage by plan.",
    labelnames=("plan",),
)
QUOTA_LIMIT = Gauge(
    "coverai_quota_limit",
    "Current quota limit by plan. Pro is exported as -1 for unlimited.",
    labelnames=("plan",),
)


def initialize_generation_metrics() -> None:
    """Инициализирует generation metrics."""
    for plan in Plan:
        QUOTA_USAGE.labels(plan=plan.value).set(0)
        QUOTA_LIMIT.labels(plan=plan.value).set(-1 if plan == Plan.PRO else 0)
        for status in GenerationStatus:
            GENERATION_REQUESTS_TOTAL.labels(
                status=status.value,
                plan=plan.value,
            ).inc(0)


def record_generation(status: GenerationStatus, plan: Plan) -> None:
    """Записывает метрику генерации."""
    GENERATION_REQUESTS_TOTAL.labels(
        status=status.value,
        plan=plan.value,
    ).inc()


def observe_generation_latency(seconds: float) -> None:
    """Записывает latency генерации."""
    GENERATION_LATENCY_SECONDS.observe(seconds)


def observe_hh_latency(seconds: float) -> None:
    """Записывает latency hh.ru."""
    HH_LATENCY_SECONDS.observe(seconds)


def set_quota_usage(plan: Plan, used: int, limit: int | None) -> None:
    """Обновляет метрику использования квоты."""
    QUOTA_USAGE.labels(plan=plan.value).set(used)
    QUOTA_LIMIT.labels(plan=plan.value).set(limit if limit is not None else -1)
