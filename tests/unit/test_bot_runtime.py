from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from coverai.bot import runtime
from coverai.bot.runtime import RuntimeBotUseCases
from coverai.domain.enums import Tone
from coverai.services.billing.errors import InsufficientCreditsError


async def test_enqueue_generation_checks_credits_before_queue(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arq_pool = FakeArqPool()
    monkeypatch.setattr(runtime, "session_scope", fake_session_scope)

    use_cases = RuntimeBotUseCases(
        bot=object(),
        session_factory=object(),
        arq_pool=arq_pool,
    )

    with pytest.raises(InsufficientCreditsError):
        await use_cases.enqueue_generation(
            user_id=1,
            vacancy_url="https://hh.ru/vacancy/123",
            tone=Tone.FORMAL,
        )

    assert arq_pool.jobs == []


@asynccontextmanager
async def fake_session_scope(_session_factory: object) -> AsyncIterator[object]:
    yield FakeSession()


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[object, ...]]] = []

    async def enqueue_job(
        self,
        name: str,
        *args: object,
    ) -> None:
        self.jobs.append((name, args))


class FakeSession:
    async def get(self, model: object, user_id: int) -> object | None:
        return None
