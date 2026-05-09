from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from coverai.domain.enums import UserRole
from coverai.services.auth.errors import InvalidCredentialsError
from coverai.services.auth.models import TokenClaims
from coverai.services.auth.protocols import TokenSettings


def create_access_token(
    *,
    user_id: int,
    role: UserRole,
    email: str | None,
    settings: TokenSettings,
) -> str:
    """Создает access token."""
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int(
            (now + timedelta(minutes=settings.access_token_expire_minutes)).timestamp(),
        ),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str, settings: TokenSettings) -> TokenClaims:
    """Декодирует access token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
    except jwt.PyJWTError as error:
        raise InvalidCredentialsError from error

    user_id = payload.get("sub")
    role = payload.get("role")
    if not isinstance(user_id, str) or not user_id.isdecimal():
        raise InvalidCredentialsError
    if not isinstance(role, str):
        raise InvalidCredentialsError

    email = payload.get("email")
    return TokenClaims(
        user_id=int(user_id),
        role=UserRole(role),
        email=email if isinstance(email, str) else None,
    )
