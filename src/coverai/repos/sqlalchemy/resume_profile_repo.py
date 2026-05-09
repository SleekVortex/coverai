from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain import entities as domain
from coverai.infra.db import models
from coverai.repos.sqlalchemy.mappers import resume_profile_from_model


class ResumeProfileSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, profile: domain.ResumeProfile) -> domain.ResumeProfile:
        """Создает запись."""
        row = models.ResumeProfile(
            user_id=profile.user_id,
            title=profile.title,
            resume_text=profile.resume_text,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return resume_profile_from_model(row)

    async def get_by_user_id(self, user_id: int) -> domain.ResumeProfile | None:
        """Возвращает запись пользователя."""
        statement = select(models.ResumeProfile).where(
            models.ResumeProfile.user_id == user_id,
        )
        row = await self._session.scalar(statement)
        return resume_profile_from_model(row) if row else None

    async def update_text(
        self,
        profile_id: int,
        resume_text: str,
    ) -> domain.ResumeProfile | None:
        """Обновляет текст профиля."""
        row = await self._session.get(models.ResumeProfile, profile_id)
        if row is None:
            return None

        row.resume_text = resume_text
        await self._session.flush()
        await self._session.refresh(row)
        return resume_profile_from_model(row)
