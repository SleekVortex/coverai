from coverai.domain import entities as domain
from coverai.domain.enums import Plan, SubscriptionStatus
from coverai.infra.db import models


def subscription_from_model(row: models.Subscription) -> domain.Subscription:
    """Преобразует модель подписки."""
    return domain.Subscription(
        id=row.id,
        user_id=row.user_id,
        plan=Plan(row.plan),
        status=SubscriptionStatus(row.status),
        starts_at=row.starts_at,
        expires_at=row.expires_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
