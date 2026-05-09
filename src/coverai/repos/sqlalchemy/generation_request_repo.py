from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain import entities as domain
from coverai.domain.enums import GenerationStatus
from coverai.infra.db import models
from coverai.repos.sqlalchemy.mappers import generation_request_from_model


class GenerationRequestSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        request: domain.GenerationRequest,
    ) -> domain.GenerationRequest:
        """Создает запись."""
        row = models.GenerationRequest(
            user_id=request.user_id,
            profile_id=request.profile_id,
            vacancy_id=request.vacancy_id,
            status=request.status.value,
            tone=request.tone.value,
            error_message=request.error_message,
            snapshot_profile_text=request.snapshot_profile_text,
            snapshot_vacancy_text=request.snapshot_vacancy_text,
            snapshot_tone=(
                request.snapshot_tone.value if request.snapshot_tone else None
            ),
            completed_at=request.completed_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return generation_request_from_model(row)

    async def get_by_id(self, request_id: int) -> domain.GenerationRequest | None:
        """Возвращает запись по id."""
        row = await self._session.get(models.GenerationRequest, request_id)
        return generation_request_from_model(row) if row else None

    async def get_by_id_for_user(
        self,
        request_id: int,
        user_id: int,
    ) -> domain.GenerationRequest | None:
        """Возвращает запись пользователя по id."""
        statement = select(models.GenerationRequest).where(
            models.GenerationRequest.id == request_id,
            models.GenerationRequest.user_id == user_id,
        )
        row = await self._session.scalar(statement)
        return generation_request_from_model(row) if row else None

    async def update_status(
        self,
        request_id: int,
        status: GenerationStatus,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> domain.GenerationRequest | None:
        """Обновляет статус записи."""
        row = await self._session.get(models.GenerationRequest, request_id)
        if row is None:
            return None

        row.status = status.value
        row.error_message = error_message
        row.completed_at = completed_at
        await self._session.flush()
        await self._session.refresh(row)
        return generation_request_from_model(row)

    async def count_by_user_statuses_since(
        self,
        user_id: int,
        statuses: set[GenerationStatus],
        since: datetime,
    ) -> int:
        """Считает записи по статусам за период."""
        statement = (
            select(func.count())
            .select_from(models.GenerationRequest)
            .where(
                models.GenerationRequest.user_id == user_id,
                models.GenerationRequest.status.in_(
                    status.value for status in statuses
                ),
                models.GenerationRequest.created_at >= since,
            )
        )
        count = await self._session.scalar(statement)
        return int(count or 0)
