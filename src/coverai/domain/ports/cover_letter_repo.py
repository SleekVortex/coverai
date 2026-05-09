from datetime import datetime
from typing import Protocol, runtime_checkable

from coverai.domain.entities import CoverLetter


@runtime_checkable
class CoverLetterRepo(Protocol):
    async def create(self, letter: CoverLetter) -> CoverLetter:
        """Создает запись."""
        ...

    async def get_by_id(self, letter_id: int) -> CoverLetter | None:
        """Возвращает запись по id."""
        ...

    async def list_by_user_id(
        self, user_id: int, limit: int = 20
    ) -> list[CoverLetter]:
        """Возвращает записи пользователя."""
        ...

    async def list_by_user_id_since(
        self,
        user_id: int,
        since: datetime | None,
        limit: int = 20,
    ) -> list[CoverLetter]:
        """Возвращает записи пользователя за период."""
        ...
