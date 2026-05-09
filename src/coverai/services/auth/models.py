from dataclasses import dataclass

from coverai.domain.enums import UserRole


@dataclass(frozen=True, slots=True)
class TokenClaims:
    user_id: int
    role: UserRole
    email: str | None

