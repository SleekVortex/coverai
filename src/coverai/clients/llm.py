from time import perf_counter
from typing import cast

import httpx

from coverai.domain.llm import LLMClientError, LLMCompletion


class HttpxLLMClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        max_tokens: int | None = None,
        proxy_url: str = "",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            proxy=proxy_url or None,
            timeout=60.0,
        )

    async def generate_cover_letter(self, prompt: str) -> LLMCompletion:
        """Генерирует сопроводительное письмо."""
        started_at = perf_counter()
        payload: dict[str, object] = {
            "model": self._model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
        }
        if self._max_tokens is not None:
            payload["max_tokens"] = self._max_tokens

        try:
            response = await self._client.post("/chat/completions", json=payload)
        except httpx.TimeoutException as error:
            raise LLMClientError("LLM request timed out") from error
        except httpx.HTTPError as error:
            raise LLMClientError(str(error)) from error

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise LLMClientError(str(error)) from error

        try:
            response_payload = response.json()
        except ValueError as error:
            raise LLMClientError("LLM provider returned invalid JSON") from error

        if not isinstance(response_payload, dict):
            raise LLMClientError("LLM provider returned non-object JSON")

        generation_ms = int((perf_counter() - started_at) * 1000)
        return LLMCompletion(
            text=message_content(cast("dict[str, object]", response_payload)),
            model=response_model(
                cast("dict[str, object]", response_payload),
                fallback=self._model,
            ),
            generation_ms=generation_ms,
        )

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        if self._owns_client:
            await self._client.aclose()


def message_content(payload: dict[str, object]) -> str:
    """Извлекает содержимое сообщения."""
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise LLMClientError("LLM response misses choices")

    first_choice = choices[0]
    if not isinstance(first_choice, dict):
        raise LLMClientError("LLM response has invalid choice")

    message = first_choice.get("message")
    if not isinstance(message, dict):
        raise LLMClientError("LLM response misses message")

    content = message.get("content")
    if not isinstance(content, str):
        raise LLMClientError("LLM response misses message content")

    return content


def response_model(payload: dict[str, object], fallback: str) -> str:
    """Извлекает модель ответа."""
    model = payload.get("model")
    return model if isinstance(model, str) and model else fallback
