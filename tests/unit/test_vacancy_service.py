from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from fakes.repos import FakeVacancyRepo

from coverai.domain.entities import Employer, Vacancy
from coverai.domain.hh import HHEmployerPayload, HHVacancyPayload
from coverai.services.vacancy import VacancyService
from coverai.services.vacancy.errors import VacancyClosedError


async def test_loads_missing_vacancy_from_hh_and_caches_it() -> None:
    repo = FakeVacancyRepo()
    client = FakeHHClient()
    now = datetime(2026, 5, 2, tzinfo=UTC)
    service = VacancyService(repo, client, FrozenClock(now))

    result = await service.get_or_load_vacancy("https://hh.ru/vacancy/123")

    assert result.from_cache is False
    assert result.vacancy.hh_id == 123
    assert result.vacancy.title == "Python Developer"
    assert result.vacancy.cached_at == now
    assert result.employer.hh_id == 456
    assert result.employer.cached_at == now
    assert client.vacancy_calls == [123]
    assert client.employer_calls == [456]


async def test_uses_fresh_cache_without_hh_calls() -> None:
    repo = FakeVacancyRepo()
    now = datetime(2026, 5, 2, tzinfo=UTC)
    employer = await repo.create_employer(
        Employer(hh_id=456, name="Cached Employer", cached_at=now),
    )
    vacancy = await repo.create_vacancy(
        Vacancy(
            hh_id=123,
            employer_id=required_id(employer),
            title="Cached Vacancy",
            cached_at=now,
        ),
    )
    client = FakeHHClient()
    service = VacancyService(repo, client, FrozenClock(now))

    result = await service.get_or_load_vacancy("https://hh.ru/vacancy/123")

    assert result.from_cache is True
    assert result.vacancy == vacancy
    assert result.employer == employer
    assert client.vacancy_calls == []
    assert client.employer_calls == []


async def test_updates_stale_cache() -> None:
    repo = FakeVacancyRepo()
    now = datetime(2026, 5, 2, tzinfo=UTC)
    stale_at = now - timedelta(hours=2)
    employer = await repo.create_employer(
        Employer(hh_id=456, name="Old Employer", cached_at=stale_at),
    )
    vacancy = await repo.create_vacancy(
        Vacancy(
            hh_id=123,
            employer_id=required_id(employer),
            title="Old Vacancy",
            cached_at=stale_at,
        ),
    )
    client = FakeHHClient()
    service = VacancyService(repo, client, FrozenClock(now))

    result = await service.get_or_load_vacancy("https://hh.ru/vacancy/123")

    assert result.from_cache is False
    assert result.vacancy.id == vacancy.id
    assert result.vacancy.title == "Python Developer"
    assert result.vacancy.cached_at == now
    assert result.employer.id == employer.id
    assert result.employer.name == "Example Inc"
    assert result.employer.cached_at == now
    assert client.vacancy_calls == [123]
    assert client.employer_calls == [456]


async def test_refreshes_placeholder_vacancy_with_real_employer() -> None:
    repo = FakeVacancyRepo()
    now = datetime(2026, 5, 2, tzinfo=UTC)
    placeholder_employer = await repo.create_employer(
        Employer(hh_id=-123, name="Pending employer", cached_at=None),
    )
    await repo.create_vacancy(
        Vacancy(
            hh_id=123,
            employer_id=required_id(placeholder_employer),
            title="Pending vacancy",
            cached_at=None,
        ),
    )
    client = FakeHHClient()
    service = VacancyService(repo, client, FrozenClock(now))

    result = await service.get_or_load_vacancy("https://hh.ru/vacancy/123")

    assert result.from_cache is False
    assert result.employer.hh_id == 456
    assert result.vacancy.employer_id == required_id(result.employer)
    assert result.vacancy.cached_at == now


async def test_rejects_archived_vacancy() -> None:
    client = FakeHHClient(
        vacancy_payload=vacancy_payload(archived=True, type_id="open"),
    )
    service = VacancyService(FakeVacancyRepo(), client, FrozenClock())

    with pytest.raises(VacancyClosedError):
        await service.get_or_load_vacancy("https://hh.ru/vacancy/123")

    assert client.employer_calls == []


async def test_rejects_non_open_vacancy() -> None:
    client = FakeHHClient(
        vacancy_payload=vacancy_payload(archived=False, type_id="closed"),
    )
    service = VacancyService(FakeVacancyRepo(), client, FrozenClock())

    with pytest.raises(VacancyClosedError):
        await service.get_or_load_vacancy("https://hh.ru/vacancy/123")

    assert client.employer_calls == []


class FakeHHClient:
    def __init__(
        self,
        vacancy_payload: HHVacancyPayload | None = None,
        employer_payload: HHEmployerPayload | None = None,
    ) -> None:
        self.vacancy_payload = vacancy_payload or vacancy_payload_default()
        self.employer_payload = employer_payload or employer_payload_default()
        self.vacancy_calls: list[int] = []
        self.employer_calls: list[int] = []

    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        self.vacancy_calls.append(hh_id)
        return self.vacancy_payload

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        self.employer_calls.append(hh_id)
        return self.employer_payload


@dataclass(frozen=True, slots=True)
class FrozenClock:
    current: datetime = datetime(2026, 5, 2, tzinfo=UTC)

    def now(self) -> datetime:
        return self.current


def vacancy_payload_default() -> HHVacancyPayload:
    return vacancy_payload(archived=False, type_id="open")


def vacancy_payload(archived: object, type_id: str | None) -> HHVacancyPayload:
    return HHVacancyPayload(
        hh_id=123,
        title="Python Developer",
        employer_hh_id=456,
        employer_name="Example Inc",
        url="https://hh.ru/vacancy/123",
        archived=archived,
        type_id=type_id,
        raw_payload={"id": "123", "name": "Python Developer"},
    )


def employer_payload_default() -> HHEmployerPayload:
    return HHEmployerPayload(
        hh_id=456,
        name="Example Inc",
        url="https://hh.ru/employer/456",
        raw_payload={"id": "456", "name": "Example Inc"},
    )


def required_id(entity: Employer | Vacancy) -> int:
    if entity.id is None:
        raise AssertionError("entity id is not assigned")

    return entity.id
