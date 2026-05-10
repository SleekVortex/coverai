from coverai.domain.entities import User
from coverai.domain.enums import Plan
from coverai.domain.ports import UserRepo
from coverai.services.users.errors import UserNotFoundError


class UserService:
    def __init__(self, user_repo: UserRepo) -> None:
        self._user_repo = user_repo

    async def get_by_id(self, user_id: int) -> User:
        """Возвращает пользователя по id."""
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError
        return user

    async def get_by_email(self, email: str) -> User | None:
        """Возвращает пользователя по email."""
        return await self._user_repo.get_by_email(email)

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str | None = None,
    ) -> User:
        """Возвращает или создает пользователя."""
        existing = await self._user_repo.get_by_telegram_id(telegram_id)
        if existing is not None:
            return existing

        return await self._user_repo.create(
            User(
                telegram_id=telegram_id,
                plan=Plan.FREE,
                username=username,
                first_name=first_name,
                language_code=language_code,
            ),
        )
