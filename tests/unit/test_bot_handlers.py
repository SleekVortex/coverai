from dataclasses import dataclass
from datetime import UTC, datetime

import pytest

from coverai.bot.handlers import (
    MAIN_MENU_HISTORY,
    MAIN_MENU_PLAN,
    MAIN_MENU_PROFILE,
    PendingToneStore,
    handle_document,
    handle_history_command,
    handle_plan_command,
    handle_profile_command,
    handle_start,
    handle_text_message,
    handle_tone_callback,
)
from coverai.domain.entities import CoverLetter, ResumeProfile, User
from coverai.domain.enums import Plan, Tone
from coverai.services.billing import PlanUsage
from coverai.services.billing.errors import InsufficientCreditsError, QuotaExceededError
from coverai.services.history import HistoryResult
from coverai.services.history.errors import HistoryAccessDeniedError
from coverai.services.profile import ProfileResult
from coverai.services.profile.errors import (
    ProfileNotFoundError,
    ResumeTextTooShortError,
)


@dataclass(frozen=True, slots=True)
class FakeTelegramUser:
    id: int = 1001
    username: str | None = "tester"
    first_name: str | None = "Test"
    language_code: str | None = "ru"


@dataclass(frozen=True, slots=True)
class FakeDocument:
    file_id: str
    file_name: str | None


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    reply_markup: object | None


class FakeMessage:
    def __init__(
        self,
        text: str | None = None,
        document: FakeDocument | None = None,
        from_user: FakeTelegramUser | None = None,
    ) -> None:
        self.text = text
        self.document = document
        self.from_user = from_user or FakeTelegramUser()
        self.answers: list[Answer] = []

    async def answer(
        self,
        text: str,
        reply_markup: object | None = None,
    ) -> object:
        self.answers.append(Answer(text=text, reply_markup=reply_markup))
        return object()


class FakeCallback:
    def __init__(
        self,
        data: str | None,
        message: FakeMessage | None,
        from_user: FakeTelegramUser | None = None,
    ) -> None:
        self.data = data
        self.message = message
        self.from_user = from_user or FakeTelegramUser()
        self.answers: list[str | None] = []

    async def answer(
        self,
        text: str | None = None,
        show_alert: bool | None = None,
    ) -> object:
        self.answers.append(text)
        return object()


class FakeBotUseCases:
    def __init__(
        self,
        plan: Plan = Plan.FREE,
        has_profile: bool = True,
        save_error: Exception | None = None,
        enqueue_error: Exception | None = None,
    ) -> None:
        self.user = User(id=1, telegram_id=1001, plan=plan)
        self.credits = 10
        self.profile = ResumeProfile(
            id=2,
            user_id=1,
            resume_text="Python developer with production experience." * 4,
        )
        self.has_profile = has_profile
        self.save_error = save_error
        self.enqueue_error = enqueue_error
        self.enqueued: list[tuple[int, str, Tone]] = []
        self.saved_files: list[tuple[int, str, str]] = []
        self.saved_texts: list[tuple[int, str]] = []
        self.history_error: Exception | None = None
        self.history_letters = [
            CoverLetter(
                id=5,
                generation_request_id=1,
                user_id=1,
                profile_id=1,
                vacancy_id=1,
                employer_id=1,
                vacancy_title="Python Developer",
                employer_name="Example LLC",
                tone=Tone.FORMAL,
                text="Saved letter",
                prompt_context="prompt",
                model="test-model",
                generation_ms=100,
            ),
        ]

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language_code: str | None,
    ) -> User:
        return self.user

    async def save_resume_text(self, user_id: int, resume_text: str) -> ProfileResult:
        if self.save_error is not None:
            raise self.save_error

        self.saved_texts.append((user_id, resume_text))
        return ProfileResult(profile=self.profile, was_truncated=False)

    async def save_resume_file(
        self,
        user_id: int,
        file_id: str,
        file_name: str,
    ) -> ProfileResult:
        self.saved_files.append((user_id, file_id, file_name))
        return ProfileResult(profile=self.profile, was_truncated=False)

    async def get_profile(self, user_id: int) -> ResumeProfile:
        if not self.has_profile:
            raise ProfileNotFoundError

        return self.profile

    async def get_plan_usage(self, user_id: int) -> PlanUsage:
        if self.user.plan == Plan.PRO:
            return PlanUsage(
                plan=self.user.plan,
                used=0,
                limit=None,
                period=None,
                period_start=None,
                subscription_expires_at=None,
            )

        return PlanUsage(
            plan=self.user.plan,
            used=1,
            limit=1,
            period="day",
            period_start=datetime.now(UTC),
            subscription_expires_at=None,
        )

    async def get_credit_balance(self, user_id: int) -> int:
        return self.credits

    async def redeem_promo_code(self, user_id: int, code: str) -> str:
        return f"redeemed {code.strip().upper()}"

    async def create_mock_top_up(self, user_id: int, credits_amount: int) -> str:
        self.credits += credits_amount
        return f"Баланс пополнен на {credits_amount} кредитов."

    async def list_history(self, user_id: int) -> HistoryResult:
        if self.history_error is not None:
            raise self.history_error

        return HistoryResult(letters=self.history_letters, cutoff=None)

    async def get_history_letter(self, user_id: int, letter_id: int) -> CoverLetter:
        if self.history_error is not None:
            raise self.history_error

        return self.history_letters[0]

    async def enqueue_generation(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
    ) -> None:
        if self.enqueue_error is not None:
            raise self.enqueue_error

        self.enqueued.append((user_id, vacancy_url, tone))


@pytest.mark.asyncio
async def test_start_shows_detailed_menu_with_command_buttons() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage(text="/start")

    await handle_start(message, use_cases)

    answer = message.answers[-1]
    assert "Как это работает" in answer.text
    assert "📄 Профиль" in answer.text
    assert answer.reply_markup is not None
    assert MAIN_MENU_PROFILE in str(answer.reply_markup)
    assert MAIN_MENU_PLAN in str(answer.reply_markup)
    assert MAIN_MENU_HISTORY in str(answer.reply_markup)


@pytest.mark.asyncio
async def test_main_menu_profile_button_opens_profile() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage(text=MAIN_MENU_PROFILE)

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.saved_texts == []
    assert "📄 Профиль" in message.answers[-1].text


@pytest.mark.asyncio
async def test_legacy_main_menu_profile_button_opens_profile() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage(text="Профиль")

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.saved_texts == []
    assert "📄 Профиль" in message.answers[-1].text


@pytest.mark.asyncio
async def test_main_menu_plan_button_opens_plan_usage() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage(text=MAIN_MENU_PLAN)

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.saved_texts == []
    assert "💰 Баланс" in message.answers[-1].text
    assert "Доступно кредитов: 10" in message.answers[-1].text


@pytest.mark.asyncio
async def test_vacancy_without_profile_asks_for_resume() -> None:
    use_cases = FakeBotUseCases(has_profile=False)
    message = FakeMessage(text="https://hh.ru/vacancy/123")

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.enqueued == []
    assert "Сначала нужен профиль" in message.answers[-1].text


@pytest.mark.asyncio
async def test_free_user_vacancy_enqueues_formal_generation() -> None:
    use_cases = FakeBotUseCases(plan=Plan.FREE)
    message = FakeMessage(text="https://hh.ru/vacancy/123")

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.enqueued == [(1, "https://hh.ru/vacancy/123", Tone.FORMAL)]
    assert message.answers[-1].reply_markup is None


@pytest.mark.asyncio
async def test_free_user_insufficient_credits_error_shows_credits_message() -> None:
    use_cases = FakeBotUseCases(enqueue_error=InsufficientCreditsError())
    message = FakeMessage(text="https://hh.ru/vacancy/123")

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.enqueued == []
    assert "Недостаточно кредитов" in message.answers[-1].text


@pytest.mark.asyncio
async def test_free_user_quota_error_shows_limit_message() -> None:
    use_cases = FakeBotUseCases(enqueue_error=QuotaExceededError())
    message = FakeMessage(text="https://hh.ru/vacancy/123")

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.enqueued == []
    assert "Лимит тарифа исчерпан" in message.answers[-1].text


@pytest.mark.parametrize("plan", [Plan.STANDARD, Plan.PRO])
@pytest.mark.asyncio
async def test_paid_user_selects_tone_before_generation(plan: Plan) -> None:
    use_cases = FakeBotUseCases(plan=plan)
    store = PendingToneStore()
    message = FakeMessage(text="https://hh.ru/vacancy/123")

    await handle_text_message(message, use_cases, store)

    assert use_cases.enqueued == []
    assert message.answers[-1].reply_markup is not None

    callback = FakeCallback(data="tone:confident", message=message)
    await handle_tone_callback(callback, use_cases, store)

    assert use_cases.enqueued == [(1, "https://hh.ru/vacancy/123", Tone.CONFIDENT)]
    assert callback.answers == ["✅ Генерация в очереди."]


@pytest.mark.asyncio
async def test_paid_user_insufficient_credits_error_shows_alert() -> None:
    use_cases = FakeBotUseCases(
        plan=Plan.STANDARD,
        enqueue_error=InsufficientCreditsError(),
    )
    store = PendingToneStore()
    store.set(1, "https://hh.ru/vacancy/123")
    message = FakeMessage(text="https://hh.ru/vacancy/123")
    callback = FakeCallback(data="tone:confident", message=message)

    await handle_tone_callback(callback, use_cases, store)

    assert use_cases.enqueued == []
    assert callback.answers == ["⚠️ Недостаточно кредитов."]


@pytest.mark.asyncio
async def test_paid_user_quota_error_shows_alert() -> None:
    use_cases = FakeBotUseCases(plan=Plan.STANDARD, enqueue_error=QuotaExceededError())
    store = PendingToneStore()
    store.set(1, "https://hh.ru/vacancy/123")
    message = FakeMessage(text="https://hh.ru/vacancy/123")
    callback = FakeCallback(data="tone:confident", message=message)

    await handle_tone_callback(callback, use_cases, store)

    assert use_cases.enqueued == []
    assert callback.answers == ["⚠️ Лимит тарифа исчерпан."]


@pytest.mark.asyncio
async def test_multiple_vacancy_links_are_rejected() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage(
        text="https://hh.ru/vacancy/123 и https://hh.ru/vacancy/456",
    )

    await handle_text_message(message, use_cases, PendingToneStore())

    assert use_cases.enqueued == []
    assert "одну ссылку" in message.answers[-1].text


@pytest.mark.asyncio
async def test_short_resume_text_error_maps_to_user_message() -> None:
    use_cases = FakeBotUseCases(save_error=ResumeTextTooShortError())
    message = FakeMessage(text="short")

    await handle_text_message(message, use_cases, PendingToneStore())

    assert "слишком короткий" in message.answers[-1].text


@pytest.mark.asyncio
async def test_document_handler_saves_resume_file() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage(document=FakeDocument(file_id="file-1", file_name="cv.pdf"))

    await handle_document(message, use_cases)

    assert use_cases.saved_files == [(1, "file-1", "cv.pdf")]
    assert "✅ Профиль сохранен" in message.answers[-1].text
    assert "ссылку на вакансию" in message.answers[-1].text


@pytest.mark.asyncio
async def test_profile_command_maps_missing_profile_to_message() -> None:
    use_cases = FakeBotUseCases(has_profile=False)
    message = FakeMessage()

    await handle_profile_command(message, use_cases)

    assert "Профиль пока не заполнен" in message.answers[-1].text


@pytest.mark.asyncio
async def test_plan_command_returns_usage() -> None:
    use_cases = FakeBotUseCases()
    message = FakeMessage()

    await handle_plan_command(message, use_cases)

    assert "💰 Баланс" in message.answers[-1].text
    assert "Доступно кредитов: 10" in message.answers[-1].text


@pytest.mark.asyncio
async def test_plan_command_formats_unlimited_plan() -> None:
    use_cases = FakeBotUseCases(plan=Plan.PRO)
    message = FakeMessage()

    await handle_plan_command(message, use_cases)

    assert "💰 Баланс" in message.answers[-1].text
    assert "Доступно кредитов: 10" in message.answers[-1].text


@pytest.mark.asyncio
async def test_history_command_shows_paid_history() -> None:
    use_cases = FakeBotUseCases(plan=Plan.PRO)
    message = FakeMessage(text="/history")

    await handle_history_command(message, use_cases)

    assert "🕘 История писем" in message.answers[-1].text
    assert "Python Developer — Example LLC" in message.answers[-1].text


@pytest.mark.asyncio
async def test_history_command_maps_free_paywall() -> None:
    use_cases = FakeBotUseCases(plan=Plan.FREE)
    use_cases.history_error = HistoryAccessDeniedError()
    message = FakeMessage(text="/history")

    await handle_history_command(message, use_cases)

    assert "Standard и Pro" in message.answers[-1].text


@pytest.mark.asyncio
async def test_history_detail_returns_letter_text() -> None:
    use_cases = FakeBotUseCases(plan=Plan.PRO)
    message = FakeMessage(text="/history 5")

    await handle_history_command(message, use_cases)

    assert "Saved letter" in message.answers[-1].text
