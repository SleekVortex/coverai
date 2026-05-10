from fastapi import APIRouter, HTTPException, Request

from coverai.api.dependencies.services import RegistrationServiceDep, UserServiceDep
from coverai.api.helpers.email import is_valid_email, normalize_email
from coverai.api.mappers.auth import token_for_user
from coverai.api.schemas import LoginRequest, RegisterRequest, TokenResponse
from coverai.services.auth import hash_password, verify_password
from coverai.services.users.errors import UserAlreadyExistsError

router = APIRouter(tags=["auth"])


@router.post("/auth/register", response_model=TokenResponse)
async def register(
    payload: RegisterRequest,
    registration_service: RegistrationServiceDep,
    request: Request,
) -> TokenResponse:
    """Регистрирует пользователя."""
    email = normalize_email(payload.email)
    if not is_valid_email(email):
        raise HTTPException(status_code=422, detail="Invalid email")

    try:
        user = await registration_service.register_api_user(
            email=email,
            password_hash=hash_password(payload.password),
        )
    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=409,
            detail="Email already registered",
        ) from error

    return token_for_user(user, request.app.state.settings)


@router.post("/auth/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    user_service: UserServiceDep,
    request: Request,
) -> TokenResponse:
    """Выдает токен доступа."""
    user = await user_service.get_by_email(normalize_email(payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return token_for_user(user, request.app.state.settings)
