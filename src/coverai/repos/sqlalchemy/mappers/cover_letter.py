from coverai.domain import entities as domain
from coverai.domain.enums import Tone
from coverai.infra.db import models


def cover_letter_from_model(row: models.CoverLetter) -> domain.CoverLetter:
    """Преобразует модель письма."""
    return domain.CoverLetter(
        id=row.id,
        generation_request_id=row.generation_request_id,
        user_id=row.user_id,
        profile_id=row.profile_id,
        vacancy_id=row.vacancy_id,
        employer_id=row.employer_id,
        vacancy_title=row.vacancy_title,
        employer_name=row.employer_name,
        tone=Tone(row.tone),
        text=row.text,
        prompt_context=row.prompt_context,
        model=row.model,
        generation_ms=row.generation_ms,
        created_at=row.created_at,
    )
