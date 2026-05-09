from typing import Protocol, runtime_checkable

from coverai.domain.entities import User


@runtime_checkable
class UserRegistrationRepo(Protocol):
    async def create(self, user: User) -> User:
        """Создает запись."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""
        ...

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Возвращает пользователя по Telegram id."""
        ...
