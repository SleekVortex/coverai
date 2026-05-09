from coverai.domain import entities as domain
from coverai.infra.db import models


def resume_profile_from_model(row: models.ResumeProfile) -> domain.ResumeProfile:
    """Преобразует модель профиля."""
    return domain.ResumeProfile(
        id=row.id,
        user_id=row.user_id,
        title=row.title,
        resume_text=row.resume_text,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
