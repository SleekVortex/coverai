from prometheus_client import Counter, Gauge

from coverai.domain.enums import Plan

PAYMENTS_TOTAL = Counter(
    "coverai_payments_total",
    "Payment intents by kind and status.",
    labelnames=("kind", "status"),
)
REVENUE_TOTAL = Counter(
    "coverai_revenue_total",
    "Recognized revenue by kind and currency.",
    labelnames=("kind", "currency"),
)
ACTIVE_SUBSCRIPTIONS = Gauge(
    "coverai_active_subscriptions",
    "Active subscriptions by paid plan.",
    labelnames=("plan",),
)
CREDITS_TOTAL = Counter(
    "coverai_credits_total",
    "Credit ledger movements by action.",
    labelnames=("action",),
)


def initialize_billing_metrics() -> None:
    """Инициализирует billing metrics."""
    for plan in (Plan.STANDARD, Plan.PRO):
        ACTIVE_SUBSCRIPTIONS.labels(plan=plan.value).set(0)
    for kind in ("topup", "subscription"):
        for status in ("pending", "succeeded", "failed", "cancelled"):
            PAYMENTS_TOTAL.labels(kind=kind, status=status).inc(0)
        REVENUE_TOTAL.labels(kind=kind, currency="USD").inc(0)
    for action in ("purchased", "spent", "refunded", "welcome_bonus"):
        CREDITS_TOTAL.labels(action=action).inc(0)


def record_payment(kind: str, status: str) -> None:
    """Записывает метрику платежа."""
    PAYMENTS_TOTAL.labels(kind=kind, status=status).inc()


def record_revenue(kind: str, currency: str, amount: float) -> None:
    """Записывает метрику выручки."""
    REVENUE_TOTAL.labels(kind=kind, currency=currency).inc(amount)


def set_active_subscriptions(plan: Plan, count: int) -> None:
    """Обновляет число активных подписок."""
    ACTIVE_SUBSCRIPTIONS.labels(plan=plan.value).set(count)


def record_credits(action: str, amount: int) -> None:
    """Записывает метрику кредитов."""
    CREDITS_TOTAL.labels(action=action).inc(amount)
