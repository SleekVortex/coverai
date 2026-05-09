from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain import entities as domain
from coverai.infra.db import models
from coverai.repos.sqlalchemy.mappers import cover_letter_from_model


class CoverLetterSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, letter: domain.CoverLetter) -> domain.CoverLetter:
        """Создает запись."""
        row = models.CoverLetter(
            generation_request_id=letter.generation_request_id,
            user_id=letter.user_id,
            profile_id=letter.profile_id,
            vacancy_id=letter.vacancy_id,
            employer_id=letter.employer_id,
            vacancy_title=letter.vacancy_title,
            employer_name=letter.employer_name,
            tone=letter.tone.value,
            text=letter.text,
            prompt_context=letter.prompt_context,
            model=letter.model,
            generation_ms=letter.generation_ms,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return cover_letter_from_model(row)

    async def get_by_id(self, letter_id: int) -> domain.CoverLetter | None:
        """Возвращает запись по id."""
        row = await self._session.get(models.CoverLetter, letter_id)
        return cover_letter_from_model(row) if row else None

    async def list_by_user_id(
        self,
        user_id: int,
        limit: int = 20,
    ) -> list[domain.CoverLetter]:
        """Возвращает записи пользователя."""
        return await self.list_by_user_id_since(
            user_id=user_id,
            since=None,
            limit=limit,
        )

    async def list_by_user_id_since(
        self,
        user_id: int,
        since: datetime | None,
        limit: int = 20,
    ) -> list[domain.CoverLetter]:
        """Возвращает записи пользователя за период."""
        statement = select(models.CoverLetter).where(
            models.CoverLetter.user_id == user_id,
        )
        if since is not None:
            statement = statement.where(models.CoverLetter.created_at >= since)

        statement = statement.order_by(
            models.CoverLetter.created_at.desc(),
            models.CoverLetter.id.desc(),
        ).limit(limit)

        rows = await self._session.scalars(statement)
        return [cover_letter_from_model(row) for row in rows]
