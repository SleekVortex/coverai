from coverai.domain import entities as domain
from coverai.domain.enums import GenerationStatus, Tone
from coverai.infra.db import models


def generation_request_from_model(
    row: models.GenerationRequest,
) -> domain.GenerationRequest:
    """Преобразует модель запроса генерации."""
    return domain.GenerationRequest(
        id=row.id,
        user_id=row.user_id,
        profile_id=row.profile_id,
        vacancy_id=row.vacancy_id,
        status=GenerationStatus(row.status),
        tone=Tone(row.tone),
        error_message=row.error_message,
        snapshot_profile_text=row.snapshot_profile_text,
        snapshot_vacancy_text=row.snapshot_vacancy_text,
        snapshot_tone=Tone(row.snapshot_tone) if row.snapshot_tone else None,
        completed_at=row.completed_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
