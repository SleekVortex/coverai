from datetime import datetime
from time import perf_counter

from coverai.domain.entities import Employer, Vacancy
from coverai.domain.hh import HHEmployerPayload, HHVacancyPayload
from coverai.domain.ids import required_id
from coverai.domain.ports import HHClient, MetricsRecorder, VacancyRepo
from coverai.services.config import SERVICE_CONFIG
from coverai.services.metrics import noop_metrics
from coverai.services.vacancy.clock import Clock, SystemClock
from coverai.services.vacancy.errors import VacancyClosedError
from coverai.services.vacancy.hh_url_parser import parse_hh_vacancy_id
from coverai.services.vacancy.models import VacancyResult

CACHE_TTL = SERVICE_CONFIG.vacancy.cache_ttl


class VacancyService:
    def __init__(
        self,
        vacancy_repo: VacancyRepo,
        hh_client: HHClient,
        clock: Clock | None = None,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self._vacancy_repo = vacancy_repo
        self._hh_client = hh_client
        self._clock = clock or SystemClock()
        self._metrics = metrics or noop_metrics

    async def get_or_load_vacancy(self, message_text: str) -> VacancyResult:
        """Возвращает или загружает вакансию."""
        started_at = perf_counter()
        try:
            hh_id = parse_hh_vacancy_id(message_text)
            now = self._clock.now()
            cached_vacancy = await self._vacancy_repo.get_by_hh_id(hh_id)

            if cached_vacancy is not None and _is_cache_fresh(
                cached_vacancy.cached_at,
                now,
            ):
                cached_employer = await self._vacancy_repo.get_employer_by_id(
                    cached_vacancy.employer_id,
                )
                if cached_employer is not None and _is_cache_fresh(
                    cached_employer.cached_at,
                    now,
                ):
                    return VacancyResult(
                        vacancy=cached_vacancy,
                        employer=cached_employer,
                        from_cache=True,
                    )

            vacancy_payload = await self._hh_client.get_vacancy(hh_id)
            _ensure_vacancy_is_open(vacancy_payload)
            employer_payload = await self._hh_client.get_employer(
                vacancy_payload.employer_hh_id,
            )

            employer = await self._upsert_employer(employer_payload, now)
            vacancy = await self._upsert_vacancy(vacancy_payload, employer, now)
            return VacancyResult(vacancy=vacancy, employer=employer, from_cache=False)
        finally:
            self._metrics.observe_hh_latency(perf_counter() - started_at)

    async def _upsert_employer(
        self,
        payload: HHEmployerPayload,
        cached_at: datetime,
    ) -> Employer:
        existing = await self._vacancy_repo.get_employer_by_hh_id(payload.hh_id)
        if existing is None:
            return await self._vacancy_repo.create_employer(
                Employer(
                    hh_id=payload.hh_id,
                    name=payload.name,
                    url=payload.url,
                    raw_payload=payload.raw_payload,
                    cached_at=cached_at,
                ),
            )

        updated = await self._vacancy_repo.update_employer_cache(
            employer_id=required_id(existing),
            name=payload.name,
            url=payload.url,
            raw_payload=payload.raw_payload,
            cached_at=cached_at,
        )
        return updated if updated is not None else existing

    async def _upsert_vacancy(
        self,
        payload: HHVacancyPayload,
        employer: Employer,
        cached_at: datetime,
    ) -> Vacancy:
        existing = await self._vacancy_repo.get_by_hh_id(payload.hh_id)
        if existing is None:
            return await self._vacancy_repo.create_vacancy(
                Vacancy(
                    hh_id=payload.hh_id,
                    employer_id=required_id(employer),
                    title=payload.title,
                    url=payload.url,
                    raw_payload=payload.raw_payload,
                    cached_at=cached_at,
                ),
            )

        updated = await self._vacancy_repo.update_vacancy_cache(
            vacancy_id=required_id(existing),
            title=payload.title,
            url=payload.url,
            raw_payload=payload.raw_payload,
            cached_at=cached_at,
            employer_id=required_id(employer),
        )
        return updated if updated is not None else existing


def _is_cache_fresh(cached_at: datetime | None, now: datetime) -> bool:
    if cached_at is None:
        return False

    return cached_at >= now - CACHE_TTL


def _ensure_vacancy_is_open(payload: HHVacancyPayload) -> None:
    if (
        _is_truthy(payload.archived)
        or payload.type_id != SERVICE_CONFIG.vacancy.open_type_id
    ):
        raise VacancyClosedError


def _is_truthy(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() == SERVICE_CONFIG.vacancy.truthy_text

    return bool(value)
