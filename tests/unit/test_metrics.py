from prometheus_client import generate_latest
from prometheus_client.exposition import make_wsgi_app

from coverai.domain.enums import GenerationStatus, Plan
from coverai.infra.metrics import prometheus_metrics


def test_prometheus_recorder_exports_core_series() -> None:
    prometheus_metrics.record_generation(GenerationStatus.SUCCEEDED, Plan.FREE)
    prometheus_metrics.observe_generation_latency(0.5)
    prometheus_metrics.observe_hh_latency(0.1)
    prometheus_metrics.observe_llm_latency(0.4)
    prometheus_metrics.record_llm_request(
        provider="openrouter",
        model="deepseek/deepseek-chat",
        status="succeeded",
    )
    prometheus_metrics.record_llm_cost(
        provider="openrouter",
        model="deepseek/deepseek-chat",
        currency="USD",
        amount=0.01,
    )
    prometheus_metrics.set_quota_usage(Plan.FREE, used=1, limit=1)
    prometheus_metrics.set_arq_queue_size("default", 1)
    prometheus_metrics.record_payment(kind="topup", status="succeeded")
    prometheus_metrics.record_revenue(kind="topup", currency="USD", amount=10.0)
    prometheus_metrics.set_active_subscriptions(Plan.PRO, count=1)
    prometheus_metrics.record_credits(action="purchased", amount=10)

    payload = generate_latest().decode()

    assert "coverai_generation_requests_total" in payload
    assert "coverai_generation_latency_seconds" in payload
    assert "coverai_hh_latency_seconds" in payload
    assert "coverai_llm_latency_seconds" in payload
    assert "coverai_llm_requests_total" in payload
    assert "coverai_llm_cost_total" in payload
    assert "coverai_quota_usage" in payload
    assert "coverai_arq_queue_size" in payload
    assert "coverai_payments_total" in payload
    assert "coverai_revenue_total" in payload
    assert "coverai_active_subscriptions" in payload
    assert "coverai_credits_total" in payload


def test_metrics_wsgi_endpoint_contains_coverai_series() -> None:
    app = make_wsgi_app()
    response = app(
        {
            "REQUEST_METHOD": "GET",
            "PATH_INFO": "/metrics",
            "SERVER_NAME": "localhost",
            "SERVER_PORT": "8000",
            "wsgi.url_scheme": "http",
        },
        start_response,
    )
    body = b"".join(response).decode()

    assert "coverai_generation_requests_total" in body


def start_response(
    status: str,
    headers: list[tuple[str, str]],
    exc_info: object | None = None,
) -> None:
    assert status.startswith("200")
