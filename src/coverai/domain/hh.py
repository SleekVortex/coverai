from dataclasses import dataclass


class HHClientError(Exception):
    pass


class VacancyNotFoundError(HHClientError):
    pass


@dataclass(frozen=True, slots=True)
class HHVacancyPayload:
    hh_id: int
    title: str
    employer_hh_id: int
    employer_name: str
    url: str | None
    archived: object
    type_id: str | None
    raw_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class HHEmployerPayload:
    hh_id: int
    name: str
    url: str | None
    raw_payload: dict[str, object]
