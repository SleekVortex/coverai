from fastapi import APIRouter, HTTPException, Request, status

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.services import (
    GenerationQueueServiceDep,
    HistoryServiceDep,
)
from coverai.api.mappers.generations import (
    generation_status_response,
    letter_response,
)
from coverai.api.schemas import (
    CoverLetterResponse,
    GenerationCreateRequest,
    GenerationCreateResponse,
    GenerationStatusResponse,
)
from coverai.domain.ids import required_id
from coverai.services.billing.errors import (
    InsufficientCreditsError,
    QuotaExceededError,
)
from coverai.services.generation.errors import (
    ForbiddenToneError,
    GenerationRequestNotFoundError,
)
from coverai.services.history.errors import HistoryAccessDeniedError
from coverai.services.profile.errors import ProfileNotFoundError
from coverai.services.vacancy.errors import (
    InvalidVacancyUrlError,
    MultipleVacancyUrlsError,
)

router = APIRouter(tags=["generations"])


@router.post(
    "/generations",
    response_model=GenerationCreateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_generation(
    payload: GenerationCreateRequest,
    user: CurrentUserDep,
    generation_service: GenerationQueueServiceDep,
    request: Request,
) -> GenerationCreateResponse:
    """Ставит генерацию в очередь."""
    try:
        generation_request = await generation_service.enqueue_generation_for_user(
            user=user,
            vacancy_url=payload.vacancy_url,
            tone=payload.tone,
        )
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=409, detail="Profile required") from error
    except InsufficientCreditsError as error:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits",
        ) from error
    except ForbiddenToneError as error:
        raise HTTPException(status_code=403, detail="Forbidden tone") from error
    except QuotaExceededError as error:
        raise HTTPException(status_code=429, detail="Quota exceeded") from error
    except (InvalidVacancyUrlError, MultipleVacancyUrlsError) as error:
        raise HTTPException(status_code=422, detail="Invalid vacancy URL") from error

    return GenerationCreateResponse(
        queued=True,
        user_id=required_id(user),
        vacancy_url=payload.vacancy_url,
        tone=payload.tone,
        cost_credits=request.app.state.settings.billing.prediction_cost_credits,
        generation_request_id=required_id(generation_request),
        status=generation_request.status,
    )


@router.get("/generations/history", response_model=list[CoverLetterResponse])
async def generation_history(
    user: CurrentUserDep,
    history_service: HistoryServiceDep,
) -> list[CoverLetterResponse]:
    """Возвращает историю генераций."""
    try:
        history = await history_service.list_history_for_user(user)
    except HistoryAccessDeniedError as error:
        raise HTTPException(
            status_code=403,
            detail="History requires paid plan",
        ) from error
    return [letter_response(letter) for letter in history.letters]


@router.get(
    "/generations/{id}",
    response_model=GenerationStatusResponse,
)
async def generation_status(
    id: int,
    user: CurrentUserDep,
    generation_service: GenerationQueueServiceDep,
) -> GenerationStatusResponse:
    """Возвращает статус генерации."""
    try:
        generation_request = await generation_service.get_request_for_user(
            request_id=id,
            user_id=required_id(user),
        )
    except GenerationRequestNotFoundError as error:
        raise HTTPException(
            status_code=404,
            detail="Generation request not found",
        ) from error

    return generation_status_response(generation_request)
