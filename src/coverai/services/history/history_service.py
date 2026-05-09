from datetime import UTC, datetime

from coverai.domain.entities import CoverLetter
from coverai.domain.enums import Plan
from coverai.domain.ports import CoverLetterRepo, UserRepo
from coverai.services.history.errors import (
    CoverLetterNotFoundError,
    HistoryAccessDeniedError,
)
from coverai.services.history.models import (
    DEFAULT_HISTORY_LIMIT,
    STANDARD_HISTORY_PERIOD,
    HistoryResult,
)
from coverai.services.users.errors import UserNotFoundError


class HistoryService:
    def __init__(
        self,
        user_repo: UserRepo,
        cover_letter_repo: CoverLetterRepo,
    ) -> None:
        self._user_repo = user_repo
        self._cover_letter_repo = cover_letter_repo

    async def list_history(
        self,
        user_id: int,
        now: datetime | None = None,
        limit: int = DEFAULT_HISTORY_LIMIT,
    ) -> HistoryResult:
        """Возвращает историю писем."""
        cutoff = await self._history_cutoff(user_id, now)
        letters = await self._cover_letter_repo.list_by_user_id_since(
            user_id=user_id,
            since=cutoff,
            limit=limit,
        )
        return HistoryResult(letters=letters, cutoff=cutoff)

    async def get_letter(
        self,
        user_id: int,
        letter_id: int,
        now: datetime | None = None,
    ) -> CoverLetter:
        """Возвращает письмо пользователя."""
        cutoff = await self._history_cutoff(user_id, now)
        letter = await self._cover_letter_repo.get_by_id(letter_id)
        if letter is None or letter.user_id != user_id:
            raise CoverLetterNotFoundError

        if cutoff is not None and (
            letter.created_at is None or letter.created_at < cutoff
        ):
            raise CoverLetterNotFoundError

        return letter

    async def _history_cutoff(
        self,
        user_id: int,
        now: datetime | None,
    ) -> datetime | None:
        user = await self._user_repo.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError

        if user.plan == Plan.FREE:
            raise HistoryAccessDeniedError
        if user.plan == Plan.STANDARD:
            return (now or datetime.now(UTC)) - STANDARD_HISTORY_PERIOD

        return None
