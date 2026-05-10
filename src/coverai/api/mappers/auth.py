from coverai.api.schemas import TokenResponse
from coverai.configs import Settings
from coverai.domain.entities import User
from coverai.domain.enums import UserRole
from coverai.domain.ids import required_id
from coverai.services.auth import create_access_token


def token_for_user(user: User, settings: Settings) -> TokenResponse:
    """Создает token response для пользователя."""
    user_id = required_id(user)
    return TokenResponse(
        access_token=create_access_token(
            user_id=user_id,
            role=UserRole(user.role),
            email=user.email,
            settings=settings.auth,
        ),
    )
