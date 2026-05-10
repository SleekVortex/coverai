from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any, cast

import pytest

from coverai.bot.runtime import RuntimeBotUseCases
from coverai.domain.entities import User
from coverai.domain.enums import Tone
from coverai.services.billing.errors import InsufficientCreditsError
from coverai.services.generation import GenerationQueueService


async def test_enqueue_generation_delegates_user_to_service(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arq_pool = FakeArqPool()
    user = User(id=1, telegram_id=1001)
    FakeGenerationQueueService.seen = {}
    monkeypatch.setattr(RuntimeBotUseCases, "_request_scope", fake_request_scope)

    use_cases = RuntimeBotUseCases(
        bot=cast(Any, object()),
        session_factory=cast(Any, object()),
        arq_pool=cast(Any, arq_pool),
    )

    with pytest.raises(InsufficientCreditsError):
        await use_cases.enqueue_generation(
            user=user,
            vacancy_url="https://hh.ru/vacancy/123",
            tone=Tone.FORMAL,
        )

    seen = FakeGenerationQueueService.seen
    assert seen["user"] == user
    assert seen["vacancy_url"] == "https://hh.ru/vacancy/123"
    assert seen["tone"] == Tone.FORMAL
    assert arq_pool.jobs == []

@asynccontextmanager
async def fake_request_scope(
    _self: RuntimeBotUseCases,
    queue: object | None = None,
) -> AsyncIterator["FakeRequestScope"]:
    FakeGenerationQueueService.seen["queue"] = queue
    yield FakeRequestScope()


class FakeRequestScope:
    async def get(self, dependency_type: object) -> object:
        if dependency_type is GenerationQueueService:
            return FakeGenerationQueueService()
        raise LookupError(dependency_type)


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[object, ...]]] = []

    async def enqueue_job(
        self,
        name: str,
        *args: object,
    ) -> None:
        self.jobs.append((name, args))


class FakeGenerationQueueService:
    seen: dict[str, object] = {}

    def __init__(self, **kwargs: object) -> None:
        self.seen["kwargs"] = kwargs

    async def enqueue_generation_for_user(
        self,
        user: User,
        vacancy_url: str,
        tone: Tone,
    ) -> None:
        self.seen["user"] = user
        self.seen["vacancy_url"] = vacancy_url
        self.seen["tone"] = tone
        raise InsufficientCreditsError
