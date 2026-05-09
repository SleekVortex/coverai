import httpx

from coverai.clients.llm import HttpxLLMClient


class HttpxOpenRouterClient(HttpxLLMClient):
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str = "https://openrouter.ai/api/v1",
        proxy_url: str = "",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        super().__init__(
            api_key=api_key,
            model=model,
            base_url=base_url,
            proxy_url=proxy_url,
            http_client=http_client,
        )

__all__ = ["HttpxOpenRouterClient"]
