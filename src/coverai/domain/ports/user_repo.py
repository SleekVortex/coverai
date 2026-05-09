from typing import Protocol, runtime_checkable

from coverai.domain.entities import User
from coverai.domain.enums import Plan


@runtime_checkable
class UserRepo(Protocol):
    async def create(self, user: User) -> User:
        """Создает запись."""
        ...

    async def get_by_id(self, user_id: int) -> User | None:
        """Возвращает запись по id."""
        ...

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Возвращает пользователя по Telegram id."""
        ...

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""
        ...

    async def update_plan(self, user_id: int, plan: Plan) -> User | None:
        """Обновляет тариф пользователя."""
        ...

    async def update_credits(self, user_id: int, credits: int) -> User | None:
        """Обновляет баланс кредитов."""
        ...

    async def apply_credit_delta(self, user_id: int, amount: int) -> User | None:
        """Применяет изменение баланса кредитов."""
        ...
