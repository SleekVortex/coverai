from dataclasses import dataclass

from coverai.domain.entities import Employer, Vacancy


@dataclass(frozen=True, slots=True)
class VacancyResult:
    vacancy: Vacancy
    employer: Employer
    from_cache: bool

