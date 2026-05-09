from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain import entities as domain
from coverai.infra.db import models
from coverai.repos.sqlalchemy.mappers import employer_from_model, vacancy_from_model


class VacancySqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_employer(self, employer: domain.Employer) -> domain.Employer:
        """Создает работодателя."""
        row = models.Employer(
            hh_id=employer.hh_id,
            name=employer.name,
            url=employer.url,
            raw_payload=employer.raw_payload,
            cached_at=employer.cached_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return employer_from_model(row)

    async def get_employer_by_id(self, employer_id: int) -> domain.Employer | None:
        """Возвращает работодателя по id."""
        row = await self._session.get(models.Employer, employer_id)
        return employer_from_model(row) if row else None

    async def get_employer_by_hh_id(self, hh_id: int) -> domain.Employer | None:
        """Возвращает работодателя по hh id."""
        statement = select(models.Employer).where(models.Employer.hh_id == hh_id)
        row = await self._session.scalar(statement)
        return employer_from_model(row) if row else None

    async def update_employer_cache(
        self,
        employer_id: int,
        name: str,
        url: str | None,
        raw_payload: dict[str, object] | None,
        cached_at: datetime | None,
    ) -> domain.Employer | None:
        """Обновляет кэш работодателя."""
        row = await self._session.get(models.Employer, employer_id)
        if row is None:
            return None

        row.name = name
        row.url = url
        row.raw_payload = raw_payload
        row.cached_at = cached_at
        await self._session.flush()
        await self._session.refresh(row)
        return employer_from_model(row)

    async def create_vacancy(self, vacancy: domain.Vacancy) -> domain.Vacancy:
        """Создает вакансию."""
        row = models.Vacancy(
            hh_id=vacancy.hh_id,
            employer_id=vacancy.employer_id,
            title=vacancy.title,
            url=vacancy.url,
            raw_payload=vacancy.raw_payload,
            cached_at=vacancy.cached_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return vacancy_from_model(row)

    async def get_by_id(self, vacancy_id: int) -> domain.Vacancy | None:
        """Возвращает запись по id."""
        row = await self._session.get(models.Vacancy, vacancy_id)
        return vacancy_from_model(row) if row else None

    async def get_by_hh_id(self, hh_id: int) -> domain.Vacancy | None:
        """Возвращает запись по hh id."""
        statement = select(models.Vacancy).where(models.Vacancy.hh_id == hh_id)
        row = await self._session.scalar(statement)
        return vacancy_from_model(row) if row else None

    async def update_vacancy_cache(
        self,
        vacancy_id: int,
        title: str,
        url: str | None,
        raw_payload: dict[str, object] | None,
        cached_at: datetime | None,
        employer_id: int | None = None,
    ) -> domain.Vacancy | None:
        """Обновляет кэш вакансии."""
        row = await self._session.get(models.Vacancy, vacancy_id)
        if row is None:
            return None

        if employer_id is not None:
            row.employer_id = employer_id
        row.title = title
        row.url = url
        row.raw_payload = raw_payload
        row.cached_at = cached_at
        await self._session.flush()
        await self._session.refresh(row)
        return vacancy_from_model(row)
