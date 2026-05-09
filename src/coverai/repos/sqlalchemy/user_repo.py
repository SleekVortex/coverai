from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain import entities as domain
from coverai.domain.enums import Plan
from coverai.infra.db import models
from coverai.repos.sqlalchemy.mappers import user_from_model


class UserSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, user: domain.User) -> domain.User:
        """Создает запись."""
        row = models.User(
            telegram_id=user.telegram_id,
            plan=user.plan.value,
            email=user.email,
            password_hash=user.password_hash,
            role=user.role.value,
            credits=user.credits,
            pending_top_up_discount_percent=user.pending_top_up_discount_percent,
            pending_top_up_discount_valid_until=user.pending_top_up_discount_valid_until,
            pending_top_up_discount_promo_code_id=(
                user.pending_top_up_discount_promo_code_id
            ),
            username=user.username,
            first_name=user.first_name,
            language_code=user.language_code,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return user_from_model(row)

    async def get_by_id(self, user_id: int) -> domain.User | None:
        """Возвращает запись по id."""
        row = await self._session.get(models.User, user_id)
        return user_from_model(row) if row else None

    async def get_by_email(self, email: str) -> domain.User | None:
        """Возвращает пользователя по email."""
        statement = select(models.User).where(models.User.email == email)
        row = await self._session.scalar(statement)
        return user_from_model(row) if row else None

    async def get_by_telegram_id(self, telegram_id: int) -> domain.User | None:
        """Возвращает пользователя по Telegram id."""
        statement = select(models.User).where(models.User.telegram_id == telegram_id)
        row = await self._session.scalar(statement)
        return user_from_model(row) if row else None

    async def update_plan(self, user_id: int, plan: Plan) -> domain.User | None:
        """Обновляет тариф пользователя."""
        row = await self._session.get(models.User, user_id)
        if row is None:
            return None

        row.plan = plan.value
        await self._session.flush()
        await self._session.refresh(row)
        return user_from_model(row)

    async def update_credits(self, user_id: int, credits: int) -> domain.User | None:
        """Обновляет баланс кредитов."""
        row = await self._session.get(models.User, user_id)
        if row is None:
            return None

        row.credits = credits
        await self._session.flush()
        await self._session.refresh(row)
        return user_from_model(row)

    async def apply_credit_delta(
        self,
        user_id: int,
        amount: int,
    ) -> domain.User | None:
        """Применяет изменение баланса кредитов."""
        row = await self._session.get(models.User, user_id)
        if row is None:
            return None

        row.credits += amount
        await self._session.flush()
        await self._session.refresh(row)
        return user_from_model(row)
