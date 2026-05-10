from coverai.domain.entities import ResumeProfile, User
from coverai.domain.ids import required_id
from coverai.domain.ports import ResumeProfileRepo
from coverai.services.profile.errors import (
    ProfileAlreadyExistsError,
    ProfileNotFoundError,
)
from coverai.services.profile.models import ProfileResult
from coverai.services.profile.resume_text import normalize_resume_text
from coverai.services.profile.title_normalizer import normalize_profile_title


class ProfileService:
    def __init__(self, profile_repo: ResumeProfileRepo) -> None:
        self._profile_repo = profile_repo

    async def create_profile(
        self,
        user_id: int,
        title: str,
        resume_text: str,
    ) -> ProfileResult:
        """Создает профиль резюме."""
        existing = await self._profile_repo.get_by_user_id(user_id)
        if existing is not None:
            raise ProfileAlreadyExistsError

        normalized_title = normalize_profile_title(title)
        normalized_text = normalize_resume_text(resume_text)
        profile = await self._profile_repo.create(
            ResumeProfile(
                user_id=user_id,
                title=normalized_title,
                resume_text=normalized_text.text,
            ),
        )

        return ProfileResult(
            profile=profile,
            was_truncated=normalized_text.was_truncated,
        )

    async def create_profile_for_user(
        self,
        user: User,
        title: str,
        resume_text: str,
    ) -> ProfileResult:
        """Создает профиль резюме для пользователя."""
        return await self.create_profile(
            user_id=required_id(user),
            title=title,
            resume_text=resume_text,
        )

    async def get_profile(self, user_id: int) -> ResumeProfile:
        """Возвращает профиль."""
        profile = await self._profile_repo.get_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFoundError

        return profile

    async def get_profile_for_user(self, user: User) -> ResumeProfile:
        """Возвращает профиль пользователя."""
        return await self.get_profile(required_id(user))

    async def update_profile(self, user_id: int, resume_text: str) -> ProfileResult:
        """Обновляет профиль резюме."""
        profile = await self._profile_repo.get_by_user_id(user_id)
        if profile is None:
            raise ProfileNotFoundError

        normalized_text = normalize_resume_text(resume_text)
        updated = await self._profile_repo.update_text(
            profile_id=_required_profile_id(profile),
            resume_text=normalized_text.text,
        )
        if updated is None:
            raise ProfileNotFoundError

        return ProfileResult(
            profile=updated,
            was_truncated=normalized_text.was_truncated,
        )

    async def update_profile_for_user(
        self,
        user: User,
        resume_text: str,
    ) -> ProfileResult:
        """Обновляет профиль резюме пользователя."""
        return await self.update_profile(required_id(user), resume_text)


def _required_profile_id(profile: ResumeProfile) -> int:
    if profile.id is None:
        raise ProfileNotFoundError
    return profile.id
