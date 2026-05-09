from fastapi import APIRouter, HTTPException

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.api.mappers.profile import profile_response
from coverai.api.schemas import ProfileRequest, ProfileResponse
from coverai.repos.sqlalchemy import ResumeProfileSqlAlchemyRepo
from coverai.services.profile import ProfileService
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
    session: SessionDep,
) -> ProfileResponse:
    """Сохраняет профиль резюме."""
    service = ProfileService(ResumeProfileSqlAlchemyRepo(session))
    try:
        try:
            result = await service.create_profile(
                user_id=user.id,
                title=payload.title,
                resume_text=payload.resume_text,
            )
        except ProfileAlreadyExistsError:
            result = await service.update_profile(user.id, payload.resume_text)
    except InvalidProfileTitleError as error:
        raise HTTPException(status_code=422, detail="Invalid profile title") from error
    except ResumeTextTooShortError as error:
        raise HTTPException(
            status_code=422,
            detail="Resume text is too short",
        ) from error

    return profile_response(result)


@router.get("/profile", response_model=ProfileResponse)
async def get_profile(user: CurrentUserDep, session: SessionDep) -> ProfileResponse:
    """Возвращает профиль."""
    try:
        profile = await ProfileService(
            ResumeProfileSqlAlchemyRepo(session),
        ).get_profile(user.id)
    except ProfileNotFoundError as error:
        raise HTTPException(status_code=404, detail="Profile not found") from error

    return ProfileResponse(
        id=profile.id or 0,
        title=profile.title,
        resume_text=profile.resume_text,
    )
