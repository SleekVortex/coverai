import json
from typing import Any

import httpx
import pytest

from coverai.clients.llm import HttpxLLMClient


def test_llm_client_configures_proxy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen_kwargs: dict[str, Any] = {}

    class FakeAsyncClient:
        def __init__(self, **kwargs: Any) -> None:
            seen_kwargs.update(kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    HttpxLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://llm.example",
        proxy_url="http://proxy.example.test:8080",
    )

    assert seen_kwargs["proxy"] == "http://proxy.example.test:8080"


async def test_llm_client_sends_generation_limits() -> None:
    seen_payload: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen_payload.update(json.loads(request.content.decode()))
        return httpx.Response(
            status_code=200,
            json={
                "model": "test-model",
                "choices": [
                    {"message": {"content": "Здравствуйте!"}},
                ],
            },
        )

    http_client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://llm.example",
    )
    client = HttpxLLMClient(
        api_key="test-key",
        model="test-model",
        base_url="https://llm.example",
        max_tokens=2500,
        http_client=http_client,
    )

    try:
        completion = await client.generate_cover_letter("prompt")
    finally:
        await http_client.aclose()

    assert completion.text == "Здравствуйте!"
    assert seen_payload["model"] == "test-model"
    assert seen_payload["temperature"] == 0.4
    assert seen_payload["max_tokens"] == 2500
