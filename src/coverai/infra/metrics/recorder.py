from coverai.domain.enums import GenerationStatus, Plan
from coverai.infra.metrics import (
    billing_metrics,
    generation_metrics,
    llm_metrics,
    runtime_metrics,
)


class PrometheusMetricsRecorder:
    def __init__(self) -> None:
        generation_metrics.initialize_generation_metrics()
        llm_metrics.initialize_llm_metrics()
        billing_metrics.initialize_billing_metrics()
        runtime_metrics.initialize_runtime_metrics()

    def record_generation(self, status: GenerationStatus, plan: Plan) -> None:
        """Записывает метрику генерации."""
        generation_metrics.record_generation(status, plan)

    def observe_generation_latency(self, seconds: float) -> None:
        """Записывает latency генерации."""
        generation_metrics.observe_generation_latency(seconds)

    def observe_hh_latency(self, seconds: float) -> None:
        """Записывает latency hh.ru."""
        generation_metrics.observe_hh_latency(seconds)

    def observe_llm_latency(self, seconds: float) -> None:
        """Записывает latency LLM."""
        llm_metrics.observe_llm_latency(seconds)

    def record_llm_request(self, provider: str, model: str, status: str) -> None:
        """Записывает запрос к LLM."""
        llm_metrics.record_llm_request(provider, model, status)

    def record_llm_cost(
        self,
        provider: str,
        model: str,
        currency: str,
        amount: float,
    ) -> None:
        """Записывает стоимость LLM."""
        llm_metrics.record_llm_cost(provider, model, currency, amount)

    def set_quota_usage(self, plan: Plan, used: int, limit: int | None) -> None:
        """Обновляет метрику использования квоты."""
        generation_metrics.set_quota_usage(plan, used, limit)

    def set_arq_queue_size(self, queue_name: str, size: int) -> None:
        """Обновляет размер очереди ARQ."""
        runtime_metrics.set_arq_queue_size(queue_name, size)

    def record_payment(self, kind: str, status: str) -> None:
        """Записывает метрику платежа."""
        billing_metrics.record_payment(kind, status)

    def record_revenue(self, kind: str, currency: str, amount: float) -> None:
        """Записывает метрику выручки."""
        billing_metrics.record_revenue(kind, currency, amount)

    def set_active_subscriptions(self, plan: Plan, count: int) -> None:
        """Обновляет число активных подписок."""
        billing_metrics.set_active_subscriptions(plan, count)

    def record_credits(self, action: str, amount: int) -> None:
        """Записывает метрику кредитов."""
        billing_metrics.record_credits(action, amount)


prometheus_metrics = PrometheusMetricsRecorder()
