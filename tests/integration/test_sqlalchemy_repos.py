from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from itertools import count

import pytest
from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from coverai.domain import entities as domain
from coverai.domain.enums import GenerationStatus, Plan, SubscriptionStatus, Tone
from coverai.domain.user_registration_repo import UserRegistrationConflictError
from coverai.infra.db import models
from coverai.infra.db.base import Base
from coverai.infra.db.session import create_session_factory
from coverai.repos import (
    CoverLetterSqlAlchemyRepo,
    GenerationRequestSqlAlchemyRepo,
    ResumeProfileSqlAlchemyRepo,
    SubscriptionSqlAlchemyRepo,
    UserSqlAlchemyRepo,
    VacancySqlAlchemyRepo,
)

HH_IDS = count(2001)
TELEGRAM_IDS = count(1001)


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    session_factory = create_session_factory(engine)
    async with session_factory() as async_session:
        yield async_session
        await async_session.rollback()

    await engine.dispose()


async def test_user_repo_crud(session: AsyncSession) -> None:
    repo = UserSqlAlchemyRepo(session)
    user = await repo.create(
        domain.User(
            telegram_id=100,
            plan=Plan.FREE,
            username="test_user",
        ),
    )

    assert user.id is not None
    assert await repo.get_by_id(user.id) == user
    assert await repo.get_by_telegram_id(100) == user

    updated = await repo.update_plan(user.id, Plan.STANDARD)

    assert updated is not None
    assert updated.plan == Plan.STANDARD

    with pytest.raises(UserRegistrationConflictError):
        await repo.create(domain.User(telegram_id=100, plan=Plan.FREE))


async def test_resume_profile_repo_crud(session: AsyncSession) -> None:
    user = await create_user(session)
    repo = ResumeProfileSqlAlchemyRepo(session)

    profile = await repo.create(
        domain.ResumeProfile(
            user_id=required_id(user),
            title="Backend Developer",
            resume_text="initial resume",
        ),
    )

    assert profile.id is not None
    assert profile.title == "Backend Developer"
    assert await repo.get_by_user_id(required_id(user)) == profile

    updated = await repo.update_text(required_id(profile), "updated resume")

    assert updated is not None
    assert updated.title == "Backend Developer"
    assert updated.resume_text == "updated resume"

    with pytest.raises(IntegrityError):
        await repo.create(
            domain.ResumeProfile(user_id=required_id(user), resume_text="duplicate"),
        )


async def test_vacancy_repo_crud(session: AsyncSession) -> None:
    repo = VacancySqlAlchemyRepo(session)
    cached_at = datetime.now(UTC)

    employer = await repo.create_employer(
        domain.Employer(
            hh_id=200,
            name="Old Employer",
            raw_payload={"id": 200},
            cached_at=cached_at,
        ),
    )
    assert await repo.get_employer_by_hh_id(200) == employer
    assert await repo.get_employer_by_id(required_id(employer)) == employer

    updated_employer = await repo.update_employer_cache(
        required_id(employer),
        name="New Employer",
        url="https://hh.ru/employer/200",
        raw_payload={"id": 200, "name": "New Employer"},
        cached_at=cached_at + timedelta(minutes=5),
    )
    assert updated_employer is not None
    assert updated_employer.name == "New Employer"

    vacancy = await repo.create_vacancy(
        domain.Vacancy(
            hh_id=300,
            employer_id=required_id(employer),
            title="Old title",
            raw_payload={"id": 300},
            cached_at=cached_at,
        ),
    )

    assert await repo.get_by_id(required_id(vacancy)) == vacancy
    assert await repo.get_by_hh_id(300) == vacancy

    updated_vacancy = await repo.update_vacancy_cache(
        required_id(vacancy),
        title="New title",
        url="https://hh.ru/vacancy/300",
        raw_payload={"id": 300, "name": "New title"},
        cached_at=cached_at + timedelta(minutes=5),
    )

    assert updated_vacancy is not None
    assert updated_vacancy.title == "New title"

    with pytest.raises(IntegrityError):
        await repo.create_vacancy(
            domain.Vacancy(
                hh_id=300,
                employer_id=required_id(employer),
                title="Duplicate",
            ),
        )


async def test_generation_request_repo_crud(session: AsyncSession) -> None:
    user, profile, vacancy, _employer = await create_generation_prerequisites(session)
    repo = GenerationRequestSqlAlchemyRepo(session)

    request = await repo.create(
        domain.GenerationRequest(
            user_id=required_id(user),
            profile_id=required_id(profile),
            vacancy_id=required_id(vacancy),
            status=GenerationStatus.PENDING,
            tone=Tone.FORMAL,
        ),
    )

    assert request.id is not None
    assert await repo.get_by_id(request.id) == request
    assert await repo.get_by_id_for_user(request.id, required_id(user)) == request
    assert await repo.get_by_id_for_user(request.id, required_id(user) + 1) is None

    completed_at = datetime.now(UTC)
    updated = await repo.update_status(
        request.id,
        GenerationStatus.FAILED,
        error_message="llm timeout",
        completed_at=completed_at,
    )

    assert updated is not None
    assert updated.status == GenerationStatus.FAILED
    assert updated.error_message == "llm timeout"
    assert updated.completed_at is not None


async def test_generation_request_repo_counts_quota_statuses(
    session: AsyncSession,
) -> None:
    user, profile, vacancy, _employer = await create_generation_prerequisites(session)
    repo = GenerationRequestSqlAlchemyRepo(session)
    since = datetime.now(UTC) - timedelta(minutes=1)

    await repo.create(
        generation_request_input(user, profile, vacancy, GenerationStatus.PENDING),
    )
    await repo.create(
        generation_request_input(user, profile, vacancy, GenerationStatus.SUCCEEDED),
    )
    await repo.create(
        generation_request_input(user, profile, vacancy, GenerationStatus.FAILED),
    )

    count = await repo.count_by_user_statuses_since(
        user_id=required_id(user),
        statuses={GenerationStatus.PENDING, GenerationStatus.SUCCEEDED},
        since=since,
    )

    assert count == 2


async def test_cover_letter_repo_crud(session: AsyncSession) -> None:
    user, profile, vacancy, employer = await create_generation_prerequisites(session)
    request = await create_generation_request(session, user, profile, vacancy)
    repo = CoverLetterSqlAlchemyRepo(session)

    first = await repo.create(
        cover_letter_input(
            request=request,
            user=user,
            profile=profile,
            vacancy=vacancy,
            employer=employer,
            text="First letter",
        ),
    )
    second = await repo.create(
        cover_letter_input(
            request=request,
            user=user,
            profile=profile,
            vacancy=vacancy,
            employer=employer,
            text="Second letter",
        ),
    )

    assert first.id is not None
    assert await repo.get_by_id(first.id) == first
    assert await repo.list_by_user_id(required_id(user), limit=1) == [second]


async def test_cover_letter_repo_lists_history_since(session: AsyncSession) -> None:
    user, profile, vacancy, employer = await create_generation_prerequisites(session)
    request = await create_generation_request(session, user, profile, vacancy)
    repo = CoverLetterSqlAlchemyRepo(session)
    cutoff = datetime.now(UTC) - timedelta(days=30)

    old = await repo.create(
        cover_letter_input(
            request=request,
            user=user,
            profile=profile,
            vacancy=vacancy,
            employer=employer,
            text="Old letter",
        ),
    )
    recent = await repo.create(
        cover_letter_input(
            request=request,
            user=user,
            profile=profile,
            vacancy=vacancy,
            employer=employer,
            text="Recent letter",
        ),
    )
    await session.execute(
        update(models.CoverLetter)
        .where(models.CoverLetter.id == required_id(old))
        .values(created_at=cutoff - timedelta(days=1)),
    )
    await session.execute(
        update(models.CoverLetter)
        .where(models.CoverLetter.id == required_id(recent))
        .values(created_at=cutoff + timedelta(days=1)),
    )
    await session.flush()

    result = await repo.list_by_user_id_since(required_id(user), since=cutoff)

    assert [letter.text for letter in result] == ["Recent letter"]


async def test_subscription_repo_crud(session: AsyncSession) -> None:
    user = await create_user(session)
    repo = SubscriptionSqlAlchemyRepo(session)
    starts_at = datetime.now(UTC)

    old_subscription = await repo.create(
        domain.Subscription(
            user_id=required_id(user),
            plan=Plan.STANDARD,
            status=SubscriptionStatus.ACTIVE,
            starts_at=starts_at,
            expires_at=starts_at + timedelta(days=10),
        ),
    )
    new_subscription = await repo.create(
        domain.Subscription(
            user_id=required_id(user),
            plan=Plan.PRO,
            status=SubscriptionStatus.ACTIVE,
            starts_at=starts_at,
            expires_at=starts_at + timedelta(days=30),
        ),
    )

    assert await repo.get_active_by_user_id(required_id(user)) == new_subscription

    expired = await repo.update_status(
        required_id(new_subscription),
        SubscriptionStatus.EXPIRED,
    )

    assert expired is not None
    assert expired.status == SubscriptionStatus.EXPIRED
    assert await repo.get_active_by_user_id(required_id(user)) == old_subscription


async def test_subscription_repo_lists_expired_active_subscriptions(
    session: AsyncSession,
) -> None:
    user = await create_user(session)
    repo = SubscriptionSqlAlchemyRepo(session)
    now = datetime.now(UTC)
    expired = await repo.create(
        domain.Subscription(
            user_id=required_id(user),
            plan=Plan.STANDARD,
            status=SubscriptionStatus.ACTIVE,
            starts_at=now - timedelta(days=40),
            expires_at=now - timedelta(days=10),
        ),
    )
    await repo.create(
        domain.Subscription(
            user_id=required_id(user),
            plan=Plan.PRO,
            status=SubscriptionStatus.ACTIVE,
            starts_at=now,
            expires_at=now + timedelta(days=10),
        ),
    )

    assert await repo.list_active_expired_before(now) == [expired]


async def create_user(session: AsyncSession) -> domain.User:
    repo = UserSqlAlchemyRepo(session)
    return await repo.create(
        domain.User(telegram_id=next_telegram_id(), plan=Plan.FREE),
    )


async def create_generation_prerequisites(
    session: AsyncSession,
) -> tuple[domain.User, domain.ResumeProfile, domain.Vacancy, domain.Employer]:
    user = await create_user(session)
    profile = await ResumeProfileSqlAlchemyRepo(session).create(
        domain.ResumeProfile(
            user_id=required_id(user),
            title="Backend Developer",
            resume_text="resume text",
        ),
    )
    vacancy_repo = VacancySqlAlchemyRepo(session)
    employer = await vacancy_repo.create_employer(
        domain.Employer(hh_id=next_hh_id(), name="Employer"),
    )
    vacancy = await vacancy_repo.create_vacancy(
        domain.Vacancy(
            hh_id=next_hh_id(),
            employer_id=required_id(employer),
            title="Python Developer",
        ),
    )
    return user, profile, vacancy, employer


async def create_generation_request(
    session: AsyncSession,
    user: domain.User,
    profile: domain.ResumeProfile,
    vacancy: domain.Vacancy,
) -> domain.GenerationRequest:
    return await GenerationRequestSqlAlchemyRepo(session).create(
        generation_request_input(user, profile, vacancy, GenerationStatus.PENDING),
    )


def generation_request_input(
    user: domain.User,
    profile: domain.ResumeProfile,
    vacancy: domain.Vacancy,
    status: GenerationStatus,
) -> domain.GenerationRequest:
    return domain.GenerationRequest(
        user_id=required_id(user),
        profile_id=required_id(profile),
        vacancy_id=required_id(vacancy),
        status=status,
        tone=Tone.FORMAL,
    )


def cover_letter_input(
    request: domain.GenerationRequest,
    user: domain.User,
    profile: domain.ResumeProfile,
    vacancy: domain.Vacancy,
    employer: domain.Employer,
    text: str,
) -> domain.CoverLetter:
    return domain.CoverLetter(
        generation_request_id=required_id(request),
        user_id=required_id(user),
        profile_id=required_id(profile),
        vacancy_id=required_id(vacancy),
        employer_id=required_id(employer),
        vacancy_title=vacancy.title,
        employer_name=employer.name,
        tone=Tone.FORMAL,
        text=text,
        prompt_context="prompt",
        model="deepseek/deepseek-chat-v3.2",
        generation_ms=100,
    )


def required_id(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise AssertionError("entity id is not assigned")

    return entity_id


def next_telegram_id() -> int:
    return next(TELEGRAM_IDS)


def next_hh_id() -> int:
    return next(HH_IDS)
