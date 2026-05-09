from typing import Any

from coverai.domain.enums import Tone


class ArqGenerationJobQueue:
    def __init__(self, arq_pool: Any) -> None:
        self._arq_pool = arq_pool

    async def enqueue_generate_cover_letter(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
        cost_credits: int,
        generation_request_id: int | None = None,
    ) -> None:
        """Ставит задачу генерации в очередь."""
        await self._arq_pool.enqueue_job(
            "generate_cover_letter",
            user_id,
            vacancy_url,
            tone.value,
            False,
            True,
            cost_credits,
            generation_request_id,
        )
