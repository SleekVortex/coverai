from datetime import UTC, datetime, timedelta

import factory

from coverai.domain.entities import ResumeProfile, Subscription, User
from coverai.domain.enums import Plan, SubscriptionStatus


class UserFactory(factory.Factory):
    class Meta:
        model = User

    telegram_id = factory.Sequence(lambda number: 10_000 + number)
    email = factory.Sequence(lambda number: f"user{number}@example.test")
    plan = Plan.FREE
    credits = 1


class ResumeProfileFactory(factory.Factory):
    class Meta:
        model = ResumeProfile

    user_id = 1
    title = "Backend"
    resume_text = "Python backend developer " * 8


class SubscriptionFactory(factory.Factory):
    class Meta:
        model = Subscription

    user_id = 1
    plan = Plan.STANDARD
    status = SubscriptionStatus.ACTIVE
    starts_at = factory.LazyFunction(lambda: datetime.now(UTC))
    expires_at = factory.LazyAttribute(
        lambda obj: obj.starts_at + timedelta(days=30),
    )
