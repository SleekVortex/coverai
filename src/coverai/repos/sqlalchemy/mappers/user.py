from coverai.domain import entities as domain
from coverai.domain.enums import Plan, UserRole
from coverai.infra.db import models


def user_from_model(row: models.User) -> domain.User:
    """Преобразует модель пользователя."""
    return domain.User(
        id=row.id,
        telegram_id=row.telegram_id,
        plan=Plan(row.plan),
        email=row.email,
        password_hash=row.password_hash,
        role=UserRole(row.role),
        credits=row.credits,
        pending_top_up_discount_percent=row.pending_top_up_discount_percent,
        pending_top_up_discount_valid_until=row.pending_top_up_discount_valid_until,
        pending_top_up_discount_promo_code_id=row.pending_top_up_discount_promo_code_id,
        username=row.username,
        first_name=row.first_name,
        language_code=row.language_code,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
