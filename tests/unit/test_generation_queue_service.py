import pytest
from fakes.repos import (
    FakeGenerationRequestRepo,
    FakeResumeProfileRepo,
    FakeSubscriptionRepo,
    FakeUserRepo,
    FakeVacancyRepo,
    id_of,
)

from coverai.domain.entities import GenerationRequest, ResumeProfile, User
from coverai.domain.enums import GenerationStatus, Plan, Tone
from coverai.services.billing import QuotaService
from coverai.services.billing.errors import InsufficientCreditsError, QuotaExceededError
from coverai.services.generation import GenerationQueueService
from coverai.services.generation.errors import (
    ForbiddenToneError,
    GenerationRequestNotFoundError,
)
from coverai.services.profile.errors import ProfileNotFoundError
from coverai.services.vacancy.errors import InvalidVacancyUrlError


async def test_generation_queue_success_creates_pending_request_without_debit() -> None:
    service, repos, queue, user = await generation_fixture(credits=1)

    request = await service.enqueue_generation(
        user_id=id_of(user),
        vacancy_url="https://hh.ru/vacancy/123",
        tone=Tone.FORMAL,
    )

    updated_user = await repos.user_repo.get_by_id(id_of(user))
    assert request.status == GenerationStatus.PENDING
    assert request.tone == Tone.FORMAL
    assert updated_user is not None
    assert updated_user.credits == 1
    assert queue.jobs == [
        (id_of(user), "https://hh.ru/vacancy/123", Tone.FORMAL, 1, id_of(request)),
    ]


async def test_free_user_cannot_queue_confident_tone() -> None:
    service, repos, queue, user = await generation_fixture(credits=1)

    with pytest.raises(ForbiddenToneError):
        await service.enqueue_generation(
            user_id=id_of(user),
            vacancy_url="https://hh.ru/vacancy/123",
            tone=Tone.CONFIDENT,
        )

    assert repos.request_repo.requests == {}
    assert queue.jobs == []


async def test_quota_exhaustion_blocks_enqueue() -> None:
    service, repos, queue, user = await generation_fixture(credits=1)
    await repos.request_repo.create(
        GenerationRequest(
            user_id=id_of(user),
            profile_id=1,
            vacancy_id=1,
            status=GenerationStatus.PENDING,
            tone=Tone.FORMAL,
        ),
    )

    with pytest.raises(QuotaExceededError):
        await service.enqueue_generation(
            user_id=id_of(user),
            vacancy_url="https://hh.ru/vacancy/123",
            tone=Tone.FORMAL,
        )

    assert len(repos.request_repo.requests) == 1
    assert queue.jobs == []


async def test_invalid_vacancy_url_blocks_enqueue() -> None:
    service, repos, queue, user = await generation_fixture(credits=1)

    with pytest.raises(InvalidVacancyUrlError):
        await service.enqueue_generation(
            user_id=id_of(user),
            vacancy_url="https://example.com/vacancy/123",
            tone=Tone.FORMAL,
        )

    assert repos.request_repo.requests == {}
    assert queue.jobs == []


async def test_insufficient_credits_blocks_enqueue() -> None:
    service, repos, queue, user = await generation_fixture(credits=0)

    with pytest.raises(InsufficientCreditsError):
        await service.enqueue_generation(
            user_id=id_of(user),
            vacancy_url="https://hh.ru/vacancy/123",
            tone=Tone.FORMAL,
        )

    assert repos.request_repo.requests == {}
    assert queue.jobs == []


async def test_profile_missing_blocks_enqueue() -> None:
    service, repos, queue, user = await generation_fixture(
        credits=1,
        has_profile=False,
    )

    with pytest.raises(ProfileNotFoundError):
        await service.enqueue_generation(
            user_id=id_of(user),
            vacancy_url="https://hh.ru/vacancy/123",
            tone=Tone.FORMAL,
        )

    assert repos.request_repo.requests == {}
    assert queue.jobs == []


async def test_foreign_generation_request_is_not_returned() -> None:
    service, repos, _queue, user = await generation_fixture(credits=1)
    other = await repos.user_repo.create(User(telegram_id=200, credits=1))
    request = await repos.request_repo.create(
        GenerationRequest(
            user_id=id_of(other),
            profile_id=1,
            vacancy_id=1,
            status=GenerationStatus.PENDING,
            tone=Tone.FORMAL,
        ),
    )

    with pytest.raises(GenerationRequestNotFoundError):
        await service.get_request_for_user(
            request_id=id_of(request),
            user_id=id_of(user),
        )


async def generation_fixture(
    credits: int,
    plan: Plan = Plan.FREE,
    has_profile: bool = True,
) -> tuple[
    GenerationQueueService,
    "GenerationRepos",
    "FakeGenerationJobQueue",
    User,
]:
    repos = GenerationRepos()
    user = await repos.user_repo.create(
        User(telegram_id=100, plan=plan, credits=credits),
    )
    if has_profile:
        await repos.profile_repo.create(
            ResumeProfile(
                user_id=id_of(user),
                title="Backend",
                resume_text="Python backend developer " * 8,
            ),
        )
    queue = FakeGenerationJobQueue()
    service = GenerationQueueService(
        user_repo=repos.user_repo,
        profile_repo=repos.profile_repo,
        generation_request_repo=repos.request_repo,
        vacancy_repo=repos.vacancy_repo,
        quota_service=QuotaService(
            user_repo=repos.user_repo,
            subscription_repo=repos.subscription_repo,
            generation_request_repo=repos.request_repo,
        ),
        queue=queue,
        cost_credits=1,
    )
    return service, repos, queue, user


class GenerationRepos:
    def __init__(self) -> None:
        self.user_repo = FakeUserRepo()
        self.profile_repo = FakeResumeProfileRepo()
        self.request_repo = FakeGenerationRequestRepo()
        self.vacancy_repo = FakeVacancyRepo()
        self.subscription_repo = FakeSubscriptionRepo()


class FakeGenerationJobQueue:
    def __init__(self) -> None:
        self.jobs: list[tuple[int, str, Tone, int, int | None]] = []

    async def enqueue_generate_cover_letter(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
        cost_credits: int,
        generation_request_id: int | None = None,
    ) -> None:
        self.jobs.append(
            (user_id, vacancy_url, tone, cost_credits, generation_request_id),
        )
