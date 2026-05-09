from prometheus_client import Gauge

ARQ_QUEUE_SIZE = Gauge(
    "coverai_arq_queue_size",
    "ARQ queue size by queue name.",
    labelnames=("queue",),
)


def initialize_runtime_metrics() -> None:
    """Инициализирует runtime metrics."""
    ARQ_QUEUE_SIZE.labels(queue="default").set(0)


def set_arq_queue_size(queue_name: str, size: int) -> None:
    """Обновляет размер очереди ARQ."""
    ARQ_QUEUE_SIZE.labels(queue=queue_name).set(size)
