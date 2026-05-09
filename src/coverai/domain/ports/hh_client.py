from typing import Protocol, runtime_checkable

from coverai.domain.hh import HHEmployerPayload, HHVacancyPayload


@runtime_checkable
class HHClient(Protocol):
    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        """Возвращает вакансию."""
        ...

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        """Возвращает работодателя."""
        ...
