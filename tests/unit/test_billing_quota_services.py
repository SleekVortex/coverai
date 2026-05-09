from datetime import UTC, datetime, timedelta

import pytest
from fakes.repos import (
    FakeGenerationRequestRepo,
    FakeSubscriptionRepo,
    FakeUserRepo,
)

from coverai.domain.entities import GenerationRequest, User
from coverai.domain.enums import GenerationStatus, Plan, Tone
from coverai.services.billing import BillingService, QuotaService
from coverai.services.billing.errors import InvalidPaidPlanError, QuotaExceededError


async def test_billing_activates_standard_subscription() -> None:
    user_repo = FakeUserRepo()
    subscription_repo = FakeSubscriptionRepo()
    user = await create_user(user_repo, Plan.FREE)
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    service = BillingService(user_repo, subscription_repo)

    subscription = await service.activate_subscription(
        user_id=required_id(user),
        plan=Plan.STANDARD,
        now=now,
    )

    updated_user = await user_repo.get_by_id(required_id(user))
    assert subscription.plan == Plan.STANDARD
    assert subscription.starts_at == now
    assert subscription.expires_at == now + timedelta(days=30)
    assert updated_user is not None
    assert updated_user.plan == Plan.STANDARD


async def test_billing_rejects_free_activation() -> None:
    service = BillingService(FakeUserRepo(), FakeSubscriptionRepo())

    with pytest.raises(InvalidPaidPlanError):
        await service.activate_subscription(user_id=1, plan=Plan.FREE)


async def test_expired_subscription_returns_user_to_free() -> None:
    user_repo = FakeUserRepo()
    subscription_repo = FakeSubscriptionRepo()
    user = await create_user(user_repo, Plan.PRO)
    service = BillingService(user_repo, subscription_repo)
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)

    await service.activate_subscription(
        user_id=required_id(user),
        plan=Plan.PRO,
        now=now - timedelta(days=40),
    )

    expired = await service.expire_subscriptions(now=now)
    updated_user = await user_repo.get_by_id(required_id(user))

    assert len(expired) == 1
    assert updated_user is not None
    assert updated_user.plan == Plan.FREE


async def test_free_plan_allows_first_daily_request() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(Plan.FREE)
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)

    usage = await QuotaService(
        user_repo,
        subscription_repo,
        request_repo,
    ).ensure_can_generate(required_id(user), now)

    assert usage.used == 0
    assert usage.limit == 1
    assert usage.remaining == 1


async def test_free_plan_blocks_second_daily_request() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(Plan.FREE)
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    await create_request(request_repo, user, GenerationStatus.SUCCEEDED, now)

    with pytest.raises(QuotaExceededError):
        await QuotaService(
            user_repo,
            subscription_repo,
            request_repo,
        ).ensure_can_generate(required_id(user), now)


async def test_standard_plan_blocks_after_300_monthly_requests() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(
        Plan.STANDARD,
    )
    now = datetime(2026, 5, 20, 12, tzinfo=UTC)
    for _ in range(300):
        await create_request(request_repo, user, GenerationStatus.SUCCEEDED, now)

    with pytest.raises(QuotaExceededError):
        await QuotaService(
            user_repo,
            subscription_repo,
            request_repo,
        ).ensure_can_generate(required_id(user), now)


async def test_pro_plan_is_unlimited() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(Plan.PRO)
    now = datetime(2026, 5, 20, 12, tzinfo=UTC)
    for _ in range(100):
        await create_request(request_repo, user, GenerationStatus.SUCCEEDED, now)

    usage = await QuotaService(
        user_repo,
        subscription_repo,
        request_repo,
    ).ensure_can_generate(required_id(user), now)

    assert usage.is_unlimited is True
    assert usage.limit is None


async def test_pending_requests_count_against_quota() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(Plan.FREE)
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    await create_request(request_repo, user, GenerationStatus.PENDING, now)

    with pytest.raises(QuotaExceededError):
        await QuotaService(
            user_repo,
            subscription_repo,
            request_repo,
        ).ensure_can_generate(required_id(user), now)


async def test_moscow_day_quota_counts_utc_stored_requests() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(Plan.FREE)
    now = datetime(2026, 5, 9, 21, 10, tzinfo=UTC)
    await create_request(
        request_repo,
        user,
        GenerationStatus.PENDING,
        datetime(2026, 5, 9, 21, 5, tzinfo=UTC),
    )

    with pytest.raises(QuotaExceededError):
        await QuotaService(
            user_repo,
            subscription_repo,
            request_repo,
        ).ensure_can_generate(required_id(user), now)


async def test_failed_requests_do_not_count_against_quota() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(Plan.FREE)
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    await create_request(request_repo, user, GenerationStatus.FAILED, now)

    usage = await QuotaService(
        user_repo,
        subscription_repo,
        request_repo,
    ).ensure_can_generate(required_id(user), now)

    assert usage.used == 0
    assert usage.remaining == 1


async def test_plan_usage_contains_plan_data_for_bot_plan_command() -> None:
    user_repo, subscription_repo, request_repo, user = await quota_fixture(
        Plan.STANDARD,
    )
    now = datetime(2026, 5, 20, 12, tzinfo=UTC)
    subscription = await BillingService(
        user_repo,
        subscription_repo,
    ).activate_subscription(
        user_id=required_id(user),
        plan=Plan.STANDARD,
        now=now,
    )

    usage = await QuotaService(
        user_repo,
        subscription_repo,
        request_repo,
    ).get_plan_usage(required_id(user), now)

    assert usage.plan == Plan.STANDARD
    assert usage.limit == 300
    assert usage.period == "month"
    assert usage.subscription_expires_at == subscription.expires_at


async def quota_fixture(
    plan: Plan,
) -> tuple[FakeUserRepo, FakeSubscriptionRepo, FakeGenerationRequestRepo, User]:
    user_repo = FakeUserRepo()
    subscription_repo = FakeSubscriptionRepo()
    request_repo = FakeGenerationRequestRepo()
    user = await create_user(user_repo, plan)
    return user_repo, subscription_repo, request_repo, user


async def create_user(user_repo: FakeUserRepo, plan: Plan) -> User:
    return await user_repo.create(
        User(telegram_id=1000 + len(user_repo.users), plan=plan),
    )


async def create_request(
    request_repo: FakeGenerationRequestRepo,
    user: User,
    status: GenerationStatus,
    created_at: datetime,
) -> GenerationRequest:
    return await request_repo.create(
        GenerationRequest(
            user_id=required_id(user),
            profile_id=1,
            vacancy_id=1,
            status=status,
            tone=Tone.FORMAL,
            created_at=created_at,
        ),
    )


def required_id(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise AssertionError("entity id is not assigned")

    return entity_id
