from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest

from coverai.configs import Settings
from coverai.domain.entities import User
from coverai.domain.enums import Plan
from coverai.domain.hh import HHClientError
from coverai.services.billing.errors import QuotaExceededError
from coverai.workers import tasks


async def test_worker_notifies_user_when_hh_client_error_is_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_messages: list[tuple[int, str]] = []

    monkeypatch.setattr(tasks, "session_factory_from_context", lambda _ctx: object())
    monkeypatch.setattr(tasks, "session_scope", fake_session_scope)
    monkeypatch.setattr(tasks, "HttpxHHClient", FakeClosableClient)
    monkeypatch.setattr(tasks, "HttpxLLMClient", FakeClosableClient)
    monkeypatch.setattr(tasks, "HttpxTelegramSender", fake_sender(sent_messages))
    monkeypatch.setattr(tasks, "UserSqlAlchemyRepo", FakeUserRepo)
    monkeypatch.setattr(tasks, "ResumeProfileSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "GenerationRequestSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "CoverLetterSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "VacancySqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "SubscriptionSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "CoverLetterService", FailingCoverLetterService)

    with pytest.raises(HHClientError):
        await tasks.generate_cover_letter(
            ctx={"settings": Settings(_env_file=None)},
            user_id=1,
            vacancy_url="https://hh.ru/vacancy/123",
        )

    assert sent_messages == [(1001, tasks.HH_CLIENT_ERROR_MESSAGE)]


async def test_worker_notifies_user_when_quota_error_is_final(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent_messages: list[tuple[int, str]] = []

    monkeypatch.setattr(tasks, "session_factory_from_context", lambda _ctx: object())
    monkeypatch.setattr(tasks, "session_scope", fake_session_scope)
    monkeypatch.setattr(tasks, "HttpxHHClient", FakeClosableClient)
    monkeypatch.setattr(tasks, "HttpxLLMClient", FakeClosableClient)
    monkeypatch.setattr(tasks, "HttpxTelegramSender", fake_sender(sent_messages))
    monkeypatch.setattr(tasks, "UserSqlAlchemyRepo", FakeUserRepo)
    monkeypatch.setattr(tasks, "ResumeProfileSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "GenerationRequestSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "CoverLetterSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "VacancySqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "SubscriptionSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "CoverLetterService", QuotaFailingCoverLetterService)

    with pytest.raises(QuotaExceededError):
        await tasks.generate_cover_letter(
            ctx={"settings": Settings(_env_file=None)},
            user_id=1,
            vacancy_url="https://hh.ru/vacancy/123",
        )

    assert sent_messages == [(1001, tasks.QUOTA_EXCEEDED_MESSAGE)]


async def test_worker_passes_llm_proxy_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    llm_kwargs: dict[str, object] = {}

    class CapturingLLMClient(FakeClosableClient):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(*args, **kwargs)
            llm_kwargs.update(kwargs)

    monkeypatch.setattr(tasks, "session_factory_from_context", lambda _ctx: object())
    monkeypatch.setattr(tasks, "session_scope", fake_session_scope)
    monkeypatch.setattr(tasks, "HttpxHHClient", FakeClosableClient)
    monkeypatch.setattr(tasks, "HttpxLLMClient", CapturingLLMClient)
    monkeypatch.setattr(tasks, "HttpxTelegramSender", FakeClosableClient)
    monkeypatch.setattr(tasks, "UserSqlAlchemyRepo", FakeUserRepo)
    monkeypatch.setattr(tasks, "ResumeProfileSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "GenerationRequestSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "CoverLetterSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "VacancySqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "SubscriptionSqlAlchemyRepo", FakeRepo)
    monkeypatch.setattr(tasks, "CoverLetterService", FailingCoverLetterService)

    with pytest.raises(HHClientError):
        await tasks.generate_cover_letter(
            ctx={
                "settings": Settings(
                    _env_file=None,
                    LLM_PROXY_URL="http://proxy.example.test:8080",
                ),
            },
            user_id=1,
            vacancy_url="https://hh.ru/vacancy/123",
            notify_telegram=False,
        )

    assert llm_kwargs["proxy_url"] == "http://proxy.example.test:8080"


@asynccontextmanager
async def fake_session_scope(_session_factory: object) -> AsyncIterator[object]:
    yield object()


class FakeClosableClient:
    def __init__(self, *args: object, **kwargs: object) -> None:
        self.closed = False

    async def aclose(self) -> None:
        self.closed = True


class FakeTelegramSender(FakeClosableClient):
    def __init__(
        self,
        sent_messages: list[tuple[int, str]],
        *args: object,
        **kwargs: object,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._sent_messages = sent_messages

    async def send_message(self, telegram_id: int, text: str) -> None:
        self._sent_messages.append((telegram_id, text))


class FakeRepo:
    def __init__(self, _session: object) -> None:
        pass


class FakeUserRepo(FakeRepo):
    async def get_by_id(self, user_id: int) -> User | None:
        return User(id=user_id, telegram_id=1001, plan=Plan.FREE)


class FailingCoverLetterService:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def generate_for_vacancy_url(
        self,
        *,
        user_id: int,
        vacancy_url: str,
        tone: object,
        generation_request_id: int | None = None,
        enforce_quota: bool = True,
    ) -> object:
        raise HHClientError("hh unavailable")


class QuotaFailingCoverLetterService:
    def __init__(self, *args: object, **kwargs: object) -> None:
        pass

    async def generate_for_vacancy_url(
        self,
        *,
        user_id: int,
        vacancy_url: str,
        tone: object,
        generation_request_id: int | None = None,
        enforce_quota: bool = True,
    ) -> object:
        raise QuotaExceededError


def fake_sender(
    sent_messages: list[tuple[int, str]],
) -> type[FakeTelegramSender]:
    class BoundFakeTelegramSender(FakeTelegramSender):
        def __init__(self, *args: object, **kwargs: object) -> None:
            super().__init__(sent_messages, *args, **kwargs)

    return BoundFakeTelegramSender
