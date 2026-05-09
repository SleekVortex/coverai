from typing import cast

from coverai.domain import entities as domain
from coverai.infra.db import models


def employer_from_model(row: models.Employer) -> domain.Employer:
    """Преобразует модель работодателя."""
    return domain.Employer(
        id=row.id,
        hh_id=row.hh_id,
        name=row.name,
        url=row.url,
        raw_payload=cast("dict[str, object] | None", row.raw_payload),
        cached_at=row.cached_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
