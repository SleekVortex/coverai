from dataclasses import replace

from coverai.domain.entities import User
from coverai.domain.enums import Plan, UserRole
from coverai.domain.user_registration_repo import (
    UserRegistrationConflictError,
    UserRegistrationRepo,
)
from coverai.services.credits import CreditLedgerService
from coverai.services.users.errors import UserAlreadyExistsError


class UserRegistrationService:
    def __init__(
        self,
        user_repo: UserRegistrationRepo,
        credit_ledger_service: CreditLedgerService,
        welcome_credits: int,
    ) -> None:
        self._user_repo = user_repo
        self._credit_ledger_service = credit_ledger_service
        self._welcome_credits = welcome_credits

    async def register_api_user(self, email: str, password_hash: str) -> User:
        """Регистрирует API-пользователя."""
        existing = await self._user_repo.get_by_email(email)
        if existing is not None:
            raise UserAlreadyExistsError

        try:
            user = await self._user_repo.create(
                User(
                    telegram_id=None,
                    email=email,
                    password_hash=password_hash,
                    role=UserRole.USER,
                    plan=Plan.FREE,
                ),
            )
        except UserRegistrationConflictError as error:
            raise UserAlreadyExistsError from error
        return await self._grant_welcome_bonus(user)

    async def get_or_create_telegram_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str | None = None,
    ) -> User:
        """Возвращает или создает Telegram-пользователя."""
        existing = await self._user_repo.get_by_telegram_id(telegram_id)
        if existing is not None:
            return existing

        user = await self._user_repo.create(
            User(
                telegram_id=telegram_id,
                plan=Plan.FREE,
                username=username,
                first_name=first_name,
                language_code=language_code,
            ),
        )
        return await self._grant_welcome_bonus(user)

    async def _grant_welcome_bonus(self, user: User) -> User:
        if user.id is None:
            raise RuntimeError("user id is not assigned")

        transaction = await self._credit_ledger_service.grant_welcome_bonus(
            user_id=user.id,
            amount=self._welcome_credits,
        )
        return replace(user, credits=transaction.balance_after)
