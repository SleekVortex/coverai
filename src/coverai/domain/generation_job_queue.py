from typing import Protocol

from coverai.domain.enums import Tone


class GenerationJobQueue(Protocol):
    async def enqueue_generate_cover_letter(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
        cost_credits: int,
        generation_request_id: int | None = None,
    ) -> None:
        """Ставит задачу генерации в очередь."""
        ...
