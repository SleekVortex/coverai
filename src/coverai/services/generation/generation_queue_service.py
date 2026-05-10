from coverai.domain.entities import Employer, GenerationRequest, User, Vacancy
from coverai.domain.enums import GenerationStatus, Plan, Tone
from coverai.domain.generation_job_queue import GenerationJobQueue
from coverai.domain.ids import required_id
from coverai.domain.ports import (
    GenerationRequestRepo,
    ResumeProfileRepo,
    UserRepo,
    VacancyRepo,
)
from coverai.services.billing import QuotaService
from coverai.services.billing.errors import InsufficientCreditsError
from coverai.services.config import SERVICE_CONFIG
from coverai.services.generation.errors import (
    ForbiddenToneError,
    GenerationRequestNotFoundError,
)
from coverai.services.profile.errors import ProfileNotFoundError
from coverai.services.users.errors import UserNotFoundError
from coverai.services.vacancy import parse_hh_vacancy_id

_GENERATION_QUEUE_CONFIG = SERVICE_CONFIG.generation_queue


class GenerationQueueService:
    def __init__(
        self,
        user_repo: UserRepo,
        profile_repo: ResumeProfileRepo,
        generation_request_repo: GenerationRequestRepo,
        vacancy_repo: VacancyRepo,
        quota_service: QuotaService,
        queue: GenerationJobQueue,
        cost_credits: int,
    ) -> None:
        self._user_repo = user_repo
        self._profile_repo = profile_repo
        self._generation_request_repo = generation_request_repo
        self._vacancy_repo = vacancy_repo
        self._quota_service = quota_service
        self._queue = queue
        self._cost_credits = cost_credits

    async def enqueue_generation(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
    ) -> GenerationRequest:
        """Ставит генерацию в очередь."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        return await self._enqueue_generation_for_existing_user(
            user=user,
            user_id=user_id,
            vacancy_url=vacancy_url,
            tone=tone,
        )

    async def enqueue_generation_for_user(
        self,
        user: User,
        vacancy_url: str,
        tone: Tone,
    ) -> GenerationRequest:
        """Ставит генерацию пользователя в очередь."""
        return await self._enqueue_generation_for_existing_user(
            user=user,
            user_id=required_id(user),
            vacancy_url=vacancy_url,
            tone=tone,
        )

    async def _enqueue_generation_for_existing_user(
        self,
        user: User,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
    ) -> GenerationRequest:
        profile = await self._profile_repo.get_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFoundError

        if user.credits < self._cost_credits:
            raise InsufficientCreditsError
        if tone not in _allowed_tones(user.plan):
            raise ForbiddenToneError

        hh_id = parse_hh_vacancy_id(vacancy_url)
        await self._quota_service.ensure_can_generate(user_id)
        vacancy = await self._get_or_create_placeholder_vacancy(hh_id, vacancy_url)
        request = await self._generation_request_repo.create(
            GenerationRequest(
                user_id=user_id,
                profile_id=required_id(profile),
                vacancy_id=required_id(vacancy),
                status=GenerationStatus.PENDING,
                tone=tone,
                snapshot_profile_text=profile.resume_text,
                snapshot_vacancy_text=vacancy.title,
                snapshot_tone=tone,
            ),
        )
        await self._queue.enqueue_generate_cover_letter(
            user_id=user_id,
            vacancy_url=vacancy_url,
            tone=tone,
            cost_credits=self._cost_credits,
            generation_request_id=required_id(request),
        )
        return request

    async def get_request_for_user(
        self,
        request_id: int,
        user_id: int,
    ) -> GenerationRequest:
        """Возвращает запрос генерации пользователя."""
        request = await self._generation_request_repo.get_by_id_for_user(
            request_id=request_id,
            user_id=user_id,
        )
        if request is None:
            raise GenerationRequestNotFoundError

        return request

    async def _get_or_create_placeholder_vacancy(
        self,
        hh_id: int,
        vacancy_url: str,
    ) -> Vacancy:
        existing = await self._vacancy_repo.get_by_hh_id(hh_id)
        if existing is not None:
            return existing

        employer = await self._vacancy_repo.create_employer(
            Employer(
                hh_id=-hh_id,
                name=_GENERATION_QUEUE_CONFIG.placeholder_employer_name,
                cached_at=None,
            ),
        )
        return await self._vacancy_repo.create_vacancy(
            Vacancy(
                hh_id=hh_id,
                employer_id=required_id(employer),
                title=_GENERATION_QUEUE_CONFIG.placeholder_vacancy_title,
                url=vacancy_url,
                cached_at=None,
            ),
        )


def _allowed_tones(plan: Plan) -> set[Tone]:
    return set(_GENERATION_QUEUE_CONFIG.allowed_tones_by_plan[plan])
