from coverai.domain.enums import GenerationStatus, Plan


class NoopMetricsRecorder:
    def record_generation(self, status: GenerationStatus, plan: Plan) -> None:
        """Записывает метрику генерации."""
        pass

    def observe_generation_latency(self, seconds: float) -> None:
        """Записывает latency генерации."""
        pass

    def observe_hh_latency(self, seconds: float) -> None:
        """Записывает latency hh.ru."""
        pass

    def observe_llm_latency(self, seconds: float) -> None:
        """Записывает latency LLM."""
        pass

    def set_quota_usage(self, plan: Plan, used: int, limit: int | None) -> None:
        """Обновляет метрику использования квоты."""
        pass

    def set_arq_queue_size(self, queue_name: str, size: int) -> None:
        """Обновляет размер очереди ARQ."""
        pass


noop_metrics = NoopMetricsRecorder()
