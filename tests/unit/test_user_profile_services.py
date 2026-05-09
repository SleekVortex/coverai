import pytest
from fakes.repos import FakeCreditLedgerRepo, FakeResumeProfileRepo, FakeUserRepo

from coverai.domain.enums import Plan
from coverai.services.credits import CreditLedgerService
from coverai.services.profile import (
    MAX_RESUME_TEXT_LENGTH,
    ProfileService,
    normalize_profile_title,
    normalize_resume_text,
)
from coverai.services.profile.errors import (
    InvalidProfileTitleError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ResumeTextTooShortError,
)
from coverai.services.users import UserRegistrationService, UserService
from coverai.services.users.errors import (
    UserAlreadyExistsError,
)


async def test_get_or_create_user_creates_free_user() -> None:
    repo = FakeUserRepo()
    service = UserService(repo)

    user = await service.get_or_create_user(
        telegram_id=123,
        username="test_user",
        first_name="Test",
        language_code="ru",
    )

    assert user.id is not None
    assert user.telegram_id == 123
    assert user.plan == Plan.FREE
    assert user.username == "test_user"


async def test_get_or_create_user_reuses_existing_user() -> None:
    repo = FakeUserRepo()
    service = UserService(repo)

    created = await service.get_or_create_user(telegram_id=123, username="first")
    repeated = await service.get_or_create_user(telegram_id=123, username="second")

    assert repeated == created
    assert len(repo.users) == 1


async def test_register_api_user_grants_welcome_bonus_once() -> None:
    user_repo = FakeUserRepo()
    ledger_repo = FakeCreditLedgerRepo(user_repo)
    service = UserRegistrationService(
        user_repo=user_repo,
        credit_ledger_service=CreditLedgerService(ledger_repo),
        welcome_credits=1,
    )

    user = await service.register_api_user(
        email="user@example.test",
        password_hash="hash",
    )

    assert user.credits == 1
    assert len(ledger_repo.transactions) == 1
    assert next(iter(ledger_repo.transactions.values())).balance_after == 1

    with pytest.raises(UserAlreadyExistsError):
        await service.register_api_user(
            email="user@example.test",
            password_hash="hash",
        )

    assert len(user_repo.users) == 1
    assert len(ledger_repo.transactions) == 1


async def test_get_or_create_telegram_user_grants_welcome_bonus_once() -> None:
    user_repo = FakeUserRepo()
    ledger_repo = FakeCreditLedgerRepo(user_repo)
    service = UserRegistrationService(
        user_repo=user_repo,
        credit_ledger_service=CreditLedgerService(ledger_repo),
        welcome_credits=1,
    )

    created = await service.get_or_create_telegram_user(telegram_id=123)
    repeated = await service.get_or_create_telegram_user(telegram_id=123)

    assert created.credits == 1
    assert repeated.id == created.id
    assert repeated.credits == created.credits
    assert len(user_repo.users) == 1
    assert len(ledger_repo.transactions) == 1


async def test_create_profile_saves_normalized_title_and_resume_text() -> None:
    service = ProfileService(FakeResumeProfileRepo())

    result = await service.create_profile(
        user_id=1,
        title="  Backend Developer  ",
        resume_text=f"  {long_resume_text(120)}  ",
    )

    assert result.was_truncated is False
    assert result.profile.id is not None
    assert result.profile.user_id == 1
    assert result.profile.title == "Backend Developer"
    assert result.profile.resume_text == long_resume_text(120)


async def test_create_profile_rejects_duplicate_profile() -> None:
    service = ProfileService(FakeResumeProfileRepo())

    await service.create_profile(
        user_id=1,
        title="Backend",
        resume_text=long_resume_text(120),
    )

    with pytest.raises(ProfileAlreadyExistsError):
        await service.create_profile(
            user_id=1,
            title="Backend",
            resume_text=long_resume_text(120),
        )


async def test_get_profile_returns_existing_profile() -> None:
    service = ProfileService(FakeResumeProfileRepo())
    created = await service.create_profile(
        user_id=1,
        title="Backend",
        resume_text=long_resume_text(120),
    )

    assert await service.get_profile(user_id=1) == created.profile


async def test_get_profile_rejects_missing_profile() -> None:
    service = ProfileService(FakeResumeProfileRepo())

    with pytest.raises(ProfileNotFoundError):
        await service.get_profile(user_id=1)


async def test_update_profile_changes_resume_text_and_keeps_title() -> None:
    service = ProfileService(FakeResumeProfileRepo())
    created = await service.create_profile(
        user_id=1,
        title="Backend",
        resume_text=long_resume_text(120),
    )

    result = await service.update_profile(user_id=1, resume_text=long_resume_text(150))

    assert result.was_truncated is False
    assert result.profile.title == created.profile.title
    assert result.profile.resume_text == long_resume_text(150)


async def test_update_profile_rejects_missing_profile() -> None:
    service = ProfileService(FakeResumeProfileRepo())

    with pytest.raises(ProfileNotFoundError):
        await service.update_profile(user_id=1, resume_text=long_resume_text(150))


def test_resume_text_shorter_than_100_chars_is_rejected() -> None:
    with pytest.raises(ResumeTextTooShortError):
        normalize_resume_text("x" * 99)


def test_resume_text_longer_than_6000_chars_is_truncated() -> None:
    normalized = normalize_resume_text("x" * (MAX_RESUME_TEXT_LENGTH + 1))

    assert normalized.was_truncated is True
    assert normalized.text == "x" * MAX_RESUME_TEXT_LENGTH


def test_invalid_profile_title_is_rejected() -> None:
    with pytest.raises(InvalidProfileTitleError):
        normalize_profile_title(" ")


def long_resume_text(length: int) -> str:
    return "x" * length
