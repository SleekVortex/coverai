from fastapi import APIRouter

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.mappers.users import user_response
from coverai.api.schemas import UserResponse

router = APIRouter(tags=["users"])


@router.get("/users/me", response_model=UserResponse)
async def me(user: CurrentUserDep) -> UserResponse:
    """Возвращает текущий профиль API."""
    return user_response(user)


@router.patch("/users/me", response_model=UserResponse)
async def update_me(user: CurrentUserDep) -> UserResponse:
    """Обновляет текущего пользователя."""
    return user_response(user)
