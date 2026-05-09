from datetime import datetime
from typing import Protocol, runtime_checkable

from coverai.domain.entities import GenerationRequest
from coverai.domain.enums import GenerationStatus


@runtime_checkable
class GenerationRequestRepo(Protocol):
    async def create(self, request: GenerationRequest) -> GenerationRequest:
        """Создает запись."""
        ...

    async def get_by_id(self, request_id: int) -> GenerationRequest | None:
        """Возвращает запись по id."""
        ...

    async def get_by_id_for_user(
        self,
        request_id: int,
        user_id: int,
    ) -> GenerationRequest | None:
        """Возвращает запись пользователя по id."""
        ...

    async def update_status(
        self,
        request_id: int,
        status: GenerationStatus,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> GenerationRequest | None:
        """Обновляет статус записи."""
        ...

    async def count_by_user_statuses_since(
        self,
        user_id: int,
        statuses: set[GenerationStatus],
        since: datetime,
    ) -> int:
        """Считает записи по статусам за период."""
        ...
