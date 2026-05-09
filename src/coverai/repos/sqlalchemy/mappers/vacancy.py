from typing import cast

from coverai.domain import entities as domain
from coverai.infra.db import models


def vacancy_from_model(row: models.Vacancy) -> domain.Vacancy:
    """Преобразует модель вакансии."""
    return domain.Vacancy(
        id=row.id,
        hh_id=row.hh_id,
        employer_id=row.employer_id,
        title=row.title,
        url=row.url,
        raw_payload=cast("dict[str, object] | None", row.raw_payload),
        cached_at=row.cached_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
