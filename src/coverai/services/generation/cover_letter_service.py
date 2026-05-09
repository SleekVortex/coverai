from dataclasses import replace
from datetime import UTC, datetime
from time import perf_counter

from coverai.domain.entities import CoverLetter, GenerationRequest, ResumeProfile
from coverai.domain.enums import GenerationStatus, Tone
from coverai.domain.hh import HHClientError
from coverai.domain.llm import LLMClientError
from coverai.domain.ports import (
    CoverLetterRepo,
    GenerationRequestRepo,
    LLMClient,
    MetricsRecorder,
    ResumeProfileRepo,
    UserRepo,
)
from coverai.services.billing import QuotaService
from coverai.services.billing.errors import InsufficientCreditsError
from coverai.services.generation.errors import (
    EmptyLLMResponseError,
    GenerationRequestNotFoundError,
)
from coverai.services.generation.models import GeneratedCoverLetter
from coverai.services.metrics import noop_metrics
from coverai.services.profile.errors import ProfileNotFoundError
from coverai.services.prompts import build_cover_letter_prompt
from coverai.services.users.errors import UserNotFoundError
from coverai.services.vacancy import VacancyResult, VacancyService


class CoverLetterService:
    def __init__(
        self,
        user_repo: UserRepo,
        profile_repo: ResumeProfileRepo,
        generation_request_repo: GenerationRequestRepo,
        cover_letter_repo: CoverLetterRepo,
        vacancy_service: VacancyService,
        quota_service: QuotaService,
        llm_client: LLMClient,
        metrics: MetricsRecorder | None = None,
    ) -> None:
        self._user_repo = user_repo
        self._profile_repo = profile_repo
        self._generation_request_repo = generation_request_repo
        self._cover_letter_repo = cover_letter_repo
        self._vacancy_service = vacancy_service
        self._quota_service = quota_service
        self._llm_client = llm_client
        self._metrics = metrics or noop_metrics

    async def generate_for_vacancy_url(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone = Tone.FORMAL,
        generation_request_id: int | None = None,
        enforce_quota: bool = True,
    ) -> GeneratedCoverLetter:
        """Генерирует письмо по вакансии."""
        started_at = perf_counter()
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError
        if user.credits < 1:
            raise InsufficientCreditsError

        profile = await self._profile_repo.get_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFoundError

        request = await self._existing_request(
            generation_request_id,
            user_id,
        )
        if enforce_quota:
            await self._quota_service.ensure_can_generate(user_id)

        try:
            vacancy_result = await self._vacancy_service.get_or_load_vacancy(
                vacancy_url,
            )
            if request is None:
                request = await self._create_pending_request(
                    user_id, profile, vacancy_result, tone
                )

            letter = await self._generate_and_save_letter(
                request,
                _snapshot_profile(profile, request),
                vacancy_result,
                request.snapshot_tone or tone,
            )
        except (EmptyLLMResponseError, HHClientError, LLMClientError) as error:
            if request is not None:
                await self._mark_failed(request, error)
            self._metrics.record_generation(GenerationStatus.FAILED, user.plan)
            self._metrics.observe_generation_latency(perf_counter() - started_at)
            raise

        await self._mark_succeeded(letter.generation_request_id)
        self._metrics.record_generation(GenerationStatus.SUCCEEDED, user.plan)
        self._metrics.observe_generation_latency(perf_counter() - started_at)
        return GeneratedCoverLetter(user=user, letter=letter)

    async def _create_pending_request(
        self,
        user_id: int,
        profile: ResumeProfile,
        vacancy_result: VacancyResult,
        tone: Tone,
    ) -> GenerationRequest:
        return await self._generation_request_repo.create(
            GenerationRequest(
                user_id=user_id,
                profile_id=_required_id(profile),
                vacancy_id=_required_id(vacancy_result.vacancy),
                status=GenerationStatus.PENDING,
                tone=tone,
                snapshot_profile_text=profile.resume_text,
                snapshot_vacancy_text=vacancy_result.vacancy.title,
                snapshot_tone=tone,
            ),
        )

    async def _existing_request(
        self,
        request_id: int | None,
        user_id: int,
    ) -> GenerationRequest | None:
        if request_id is None:
            return None

        request = await self._generation_request_repo.get_by_id_for_user(
            request_id=request_id,
            user_id=user_id,
        )
        if request is None:
            raise GenerationRequestNotFoundError

        return request

    async def _generate_and_save_letter(
        self,
        request: GenerationRequest,
        profile: ResumeProfile,
        vacancy_result: VacancyResult,
        tone: Tone,
    ) -> CoverLetter:
        prompt = build_cover_letter_prompt(
            profile=profile,
            vacancy=vacancy_result.vacancy,
            employer=vacancy_result.employer,
            tone=tone,
        )
        completion = await self._llm_client.generate_cover_letter(prompt)
        self._metrics.observe_llm_latency(completion.generation_ms / 1000)
        text = completion.text.strip()
        if not text:
            raise EmptyLLMResponseError

        return await self._cover_letter_repo.create(
            CoverLetter(
                generation_request_id=_required_id(request),
                user_id=request.user_id,
                profile_id=request.profile_id,
                vacancy_id=request.vacancy_id,
                employer_id=_required_id(vacancy_result.employer),
                vacancy_title=vacancy_result.vacancy.title,
                employer_name=vacancy_result.employer.name,
                tone=tone,
                text=text,
                prompt_context=prompt,
                model=completion.model,
                generation_ms=completion.generation_ms,
            ),
        )

    async def _mark_failed(
        self,
        request: GenerationRequest,
        error: Exception,
    ) -> None:
        await self._generation_request_repo.update_status(
            request_id=_required_id(request),
            status=GenerationStatus.FAILED,
            error_message=str(error) or error.__class__.__name__,
            completed_at=datetime.now(UTC),
        )

    async def _mark_succeeded(self, request_id: int) -> None:
        await self._generation_request_repo.update_status(
            request_id=request_id,
            status=GenerationStatus.SUCCEEDED,
            completed_at=datetime.now(UTC),
        )


def _required_id(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise RuntimeError("entity id is not assigned")
    return entity_id


def _snapshot_profile(
    profile: ResumeProfile,
    request: GenerationRequest,
) -> ResumeProfile:
    if request.snapshot_profile_text is None:
        return profile

    return replace(profile, resume_text=request.snapshot_profile_text)
