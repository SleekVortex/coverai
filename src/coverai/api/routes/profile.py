from fastapi import APIRouter, HTTPException

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.services import ProfileServiceDep
from coverai.api.mappers.profile import profile_response
from coverai.api.schemas import ProfileRequest, ProfileResponse
from coverai.services.profile.errors import (
    InvalidProfileTitleError,
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
    ResumeTextTooShortError,
)

router = APIRouter(tags=["profile"])


@router.put("/profile", response_model=ProfileResponse)
async def save_profile(
    payload: ProfileRequest,
    user: CurrentUserDep,
    profile_service: ProfileServiceDep,
) -> ProfileResponse:
    """Сохраняет профиль резюме."""
    try:
        try:
            result = await profile_service.create_profile_for_user(
                user=user,
                title=payload.title,
                resume_text=payload.resume_text,
            )
        except ProfileAlreadyExistsError:
            result = await profile_service.update_profile_for_user(
                user,
                payload.resume_text,
            )
    except InvalidProfileTitleError as error:
        raise HTTPException(status_code=422, detail="Invalid profile title") from error
    except ResumeTextTooShortError as error:
        raise HTTPException(
            status_code=422,
            detail="Resume text is too short",
        ) from error

    return profile_response(result)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(
    user: CurrentUserDep,
    profile_service: ProfileServiceDep,
) -> ProfileResponse:
    """Возвращает профиль."""
    try:
        profile = await profile_service.get_profile_for_user(user)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Profile not found") from error

    return ProfileResponse(
        id=profile.id or 0,
        title=profile.title,
        resume_text=profile.resume_text,
    )
