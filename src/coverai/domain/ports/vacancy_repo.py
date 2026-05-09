from datetime import datetime
from typing import Protocol, runtime_checkable

from coverai.domain.entities import Employer, Vacancy


@runtime_checkable
class VacancyRepo(Protocol):
    async def create_employer(self, employer: Employer) -> Employer:
        """Создает работодателя."""
        ...

    async def get_employer_by_id(self, employer_id: int) -> Employer | None:
        """Возвращает работодателя по id."""
        ...

    async def get_employer_by_hh_id(self, hh_id: int) -> Employer | None:
        """Возвращает работодателя по hh id."""
        ...

    async def update_employer_cache(
        self,
        employer_id: int,
        name: str,
        url: str | None,
        raw_payload: dict[str, object] | None,
        cached_at: datetime | None,
    ) -> Employer | None:
        """Обновляет кэш работодателя."""
        ...

    async def create_vacancy(self, vacancy: Vacancy) -> Vacancy:
        """Создает вакансию."""
        ...

    async def get_by_id(self, vacancy_id: int) -> Vacancy | None:
        """Возвращает запись по id."""
        ...

    async def get_by_hh_id(self, hh_id: int) -> Vacancy | None:
        """Возвращает запись по hh id."""
        ...

    async def update_vacancy_cache(
        self,
        vacancy_id: int,
        title: str,
        url: str | None,
        raw_payload: dict[str, object] | None,
        cached_at: datetime | None,
        employer_id: int | None = None,
    ) -> Vacancy | None:
        """Обновляет кэш вакансии."""
        ...
