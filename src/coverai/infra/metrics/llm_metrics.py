from prometheus_client import Counter, Histogram

LLM_LATENCY_SECONDS = Histogram(
    "coverai_llm_latency_seconds",
    "LLM completion latency.",
)
LLM_REQUESTS_TOTAL = Counter(
    "coverai_llm_requests_total",
    "LLM requests by provider, model, and final status.",
    labelnames=("provider", "model", "status"),
)
LLM_COST_TOTAL = Counter(
    "coverai_llm_cost_total",
    "LLM usage cost by provider, model, and currency.",
    labelnames=("provider", "model", "currency"),
)


def initialize_llm_metrics() -> None:
    """Инициализирует LLM metrics."""
    for status in ("succeeded", "failed"):
        LLM_REQUESTS_TOTAL.labels(
            provider="unknown",
            model="unknown",
            status=status,
        ).inc(0)
    LLM_COST_TOTAL.labels(
        provider="unknown",
        model="unknown",
        currency="USD",
    ).inc(0)


def observe_llm_latency(seconds: float) -> None:
    """Записывает latency LLM."""
    LLM_LATENCY_SECONDS.observe(seconds)


def record_llm_request(provider: str, model: str, status: str) -> None:
    """Записывает запрос к LLM."""
    LLM_REQUESTS_TOTAL.labels(
        provider=provider,
        model=model,
        status=status,
    ).inc()


def record_llm_cost(
    provider: str,
    model: str,
    currency: str,
    amount: float,
) -> None:
    """Записывает стоимость LLM."""
    LLM_COST_TOTAL.labels(
        provider=provider,
        model=model,
        currency=currency,
    ).inc(amount)
