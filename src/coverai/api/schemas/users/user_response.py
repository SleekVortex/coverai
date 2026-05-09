from pydantic import BaseModel

from coverai.domain.enums import UserRole


class UserResponse(BaseModel):
    id: int
    email: str | None
    telegram_id: int | None
    role: UserRole
    credits: int
