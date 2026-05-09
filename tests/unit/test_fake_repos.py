from datetime import UTC, datetime, timedelta

from fakes.repos import (
    FakeCoverLetterRepo,
    FakeCreditLedgerRepo,
    FakeGenerationRequestRepo,
    FakeResumeProfileRepo,
    FakeSubscriptionRepo,
    FakeUserRepo,
    FakeVacancyRepo,
)

from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.entities import GenerationRequest, Subscription, User
from coverai.domain.enums import GenerationStatus, Plan, SubscriptionStatus, Tone
from coverai.domain.ports import (
    CoverLetterRepo,
    GenerationRequestRepo,
    ResumeProfileRepo,
    SubscriptionRepo,
    UserRepo,
    VacancyRepo,
)


def test_fake_repositories_match_protocols() -> None:
    assert isinstance(FakeUserRepo(), UserRepo)
    assert isinstance(FakeResumeProfileRepo(), ResumeProfileRepo)
    assert isinstance(FakeGenerationRequestRepo(), GenerationRequestRepo)
    assert isinstance(FakeCoverLetterRepo(), CoverLetterRepo)
    assert isinstance(FakeVacancyRepo(), VacancyRepo)
    assert isinstance(FakeSubscriptionRepo(), SubscriptionRepo)
    assert isinstance(FakeCreditLedgerRepo(FakeUserRepo()), CreditLedgerRepo)


async def test_fake_user_repo_supports_service_style_usage() -> None:
    repo: UserRepo = FakeUserRepo()
    user = await repo.create(User(telegram_id=123, plan=Plan.FREE))

    updated = await repo.update_plan(required_id(user), Plan.STANDARD)

    assert await repo.get_by_telegram_id(123) == updated
    assert updated is not None
    assert updated.plan == Plan.STANDARD


async def test_fake_generation_request_repo_updates_status() -> None:
    repo: GenerationRequestRepo = FakeGenerationRequestRepo()
    request = await repo.create(
        GenerationRequest(
            user_id=1,
            profile_id=2,
            vacancy_id=3,
            status=GenerationStatus.PENDING,
            tone=Tone.FORMAL,
        ),
    )

    updated = await repo.update_status(
        required_id(request),
        GenerationStatus.FAILED,
        error_message="hh error",
        completed_at=datetime.now(UTC),
    )

    assert updated is not None
    assert updated.status == GenerationStatus.FAILED
    assert updated.error_message == "hh error"


async def test_fake_subscription_repo_returns_active_subscription() -> None:
    repo: SubscriptionRepo = FakeSubscriptionRepo()
    starts_at = datetime.now(UTC)
    subscription = await repo.create(
        Subscription(
            user_id=1,
            plan=Plan.PRO,
            status=SubscriptionStatus.ACTIVE,
            starts_at=starts_at,
            expires_at=starts_at + timedelta(days=30),
        ),
    )

    assert await repo.get_active_by_user_id(1) == subscription

    await repo.update_status(required_id(subscription), SubscriptionStatus.EXPIRED)

    assert await repo.get_active_by_user_id(1) is None


def required_id(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise AssertionError("entity id is not assigned")

    return entity_id
