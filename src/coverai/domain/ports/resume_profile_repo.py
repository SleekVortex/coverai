from typing import Protocol, runtime_checkable

from coverai.domain.entities import ResumeProfile


@runtime_checkable
class ResumeProfileRepo(Protocol):
    async def create(self, profile: ResumeProfile) -> ResumeProfile:
        """Создает запись."""
        ...

    async def get_by_user_id(self, user_id: int) -> ResumeProfile | None:
        """Возвращает запись пользователя."""
        ...

    async def update_text(
        self,
        profile_id: int,
        resume_text: str,
    ) -> ResumeProfile | None:
        """Обновляет текст профиля."""
        ...
