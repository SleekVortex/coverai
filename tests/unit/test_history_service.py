from datetime import UTC, datetime, timedelta

import pytest
from fakes.repos import FakeCoverLetterRepo, FakeUserRepo

from coverai.domain.entities import CoverLetter, User
from coverai.domain.enums import Plan, Tone
from coverai.services.history import HistoryService
from coverai.services.history.errors import (
    CoverLetterNotFoundError,
    HistoryAccessDeniedError,
)


@pytest.mark.asyncio
async def test_free_user_cannot_view_history() -> None:
    fixture = HistoryFixture(plan=Plan.FREE)
    user = await fixture.create_user()

    with pytest.raises(HistoryAccessDeniedError):
        await fixture.service.list_history(required_id(user))


@pytest.mark.asyncio
async def test_standard_user_sees_last_30_days() -> None:
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    fixture = HistoryFixture(plan=Plan.STANDARD)
    user = await fixture.create_user()
    recent = await fixture.create_letter(
        user_id=required_id(user),
        text="recent",
        created_at=now - timedelta(days=10),
    )
    await fixture.create_letter(
        user_id=required_id(user),
        text="old",
        created_at=now - timedelta(days=31),
    )

    result = await fixture.service.list_history(required_id(user), now=now)

    assert result.cutoff == now - timedelta(days=30)
    assert result.letters == [recent]


@pytest.mark.asyncio
async def test_pro_user_sees_full_history() -> None:
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    fixture = HistoryFixture(plan=Plan.PRO)
    user = await fixture.create_user()
    recent = await fixture.create_letter(
        user_id=required_id(user),
        text="recent",
        created_at=now - timedelta(days=10),
    )
    old = await fixture.create_letter(
        user_id=required_id(user),
        text="old",
        created_at=now - timedelta(days=365),
    )

    result = await fixture.service.list_history(required_id(user), now=now)

    assert result.cutoff is None
    assert result.letters == [recent, old]


@pytest.mark.asyncio
async def test_detail_view_returns_saved_letter_text() -> None:
    fixture = HistoryFixture(plan=Plan.PRO)
    user = await fixture.create_user()
    letter = await fixture.create_letter(
        user_id=required_id(user),
        text="Saved cover letter",
        created_at=datetime(2026, 5, 2, 12, tzinfo=UTC),
    )

    result = await fixture.service.get_letter(
        user_id=required_id(user),
        letter_id=required_id(letter),
    )

    assert result.text == "Saved cover letter"


@pytest.mark.asyncio
async def test_standard_detail_denies_old_letter() -> None:
    now = datetime(2026, 5, 2, 12, tzinfo=UTC)
    fixture = HistoryFixture(plan=Plan.STANDARD)
    user = await fixture.create_user()
    letter = await fixture.create_letter(
        user_id=required_id(user),
        text="old",
        created_at=now - timedelta(days=31),
    )

    with pytest.raises(CoverLetterNotFoundError):
        await fixture.service.get_letter(
            user_id=required_id(user),
            letter_id=required_id(letter),
            now=now,
        )


class HistoryFixture:
    def __init__(self, plan: Plan) -> None:
        self.user_repo = FakeUserRepo()
        self.letter_repo = FakeCoverLetterRepo()
        self.plan = plan
        self.service = HistoryService(
            user_repo=self.user_repo,
            cover_letter_repo=self.letter_repo,
        )

    async def create_user(self) -> User:
        return await self.user_repo.create(
            User(
                telegram_id=1001,
                plan=self.plan,
            ),
        )

    async def create_letter(
        self,
        user_id: int,
        text: str,
        created_at: datetime,
    ) -> CoverLetter:
        return await self.letter_repo.create(
            CoverLetter(
                generation_request_id=1,
                user_id=user_id,
                profile_id=1,
                vacancy_id=1,
                employer_id=1,
                vacancy_title="Python Developer",
                employer_name="Example LLC",
                tone=Tone.FORMAL,
                text=text,
                prompt_context="prompt",
                model="test-model",
                generation_ms=100,
                created_at=created_at,
            ),
        )


def required_id(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise ValueError("entity id is not assigned")

    return entity_id
