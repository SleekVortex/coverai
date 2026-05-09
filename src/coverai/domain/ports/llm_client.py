from typing import Protocol, runtime_checkable

from coverai.domain.llm import LLMCompletion


@runtime_checkable
class LLMClient(Protocol):
    async def generate_cover_letter(self, prompt: str) -> LLMCompletion:
        """Генерирует сопроводительное письмо."""
        ...


OpenRouterClient = LLMClient
