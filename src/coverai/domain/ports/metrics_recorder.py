from typing import Protocol, runtime_checkable

from coverai.domain.enums import GenerationStatus, Plan


@runtime_checkable
class MetricsRecorder(Protocol):
    def record_generation(self, status: GenerationStatus, plan: Plan) -> None:
        """Записывает метрику генерации."""
        ...

    def observe_generation_latency(self, seconds: float) -> None:
        """Записывает latency генерации."""
        ...

    def observe_hh_latency(self, seconds: float) -> None:
        """Записывает latency hh.ru."""
        ...

    def observe_llm_latency(self, seconds: float) -> None:
        """Записывает latency LLM."""
        ...

    def set_quota_usage(self, plan: Plan, used: int, limit: int | None) -> None:
        """Обновляет метрику использования квоты."""
        ...

    def set_arq_queue_size(self, queue_name: str, size: int) -> None:
        """Обновляет размер очереди ARQ."""
        ...
