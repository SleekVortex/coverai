from coverai.bot.keyboards.main_menu import main_menu_keyboard
from coverai.bot.keyboards.tone import tone_keyboard
from coverai.bot.messages import (
    CREDITS_EXCEEDED_TEXT,
    GENERATION_ACCEPTED_TEXT,
    PROFILE_REQUIRED_TEXT,
    TONE_SELECT_TEXT,
)
from coverai.bot.protocols import BotUseCases, IncomingMessage
from coverai.bot.state.pending_tone_store import PendingToneStore
from coverai.domain.entities import User
from coverai.domain.enums import Plan, Tone
from coverai.services.billing.errors import InsufficientCreditsError, QuotaExceededError
from coverai.services.profile.errors import ProfileNotFoundError


async def handle_vacancy_url(
    message: IncomingMessage,
    use_cases: BotUseCases,
    pending_tones: PendingToneStore,
    user: User,
    vacancy_url: str,
) -> None:
    """Обрабатывает ссылку на вакансию."""
    try:
        await use_cases.get_profile(user)
    except ProfileNotFoundError:
        await message.answer(PROFILE_REQUIRED_TEXT, reply_markup=main_menu_keyboard())
        return

    if user.plan in {Plan.STANDARD, Plan.PRO}:
        if message.from_user is None:
            return

        pending_tones.set(message.from_user.id, vacancy_url)
        await message.answer(TONE_SELECT_TEXT, reply_markup=tone_keyboard())
        return

    try:
        await use_cases.enqueue_generation(user, vacancy_url, Tone.FORMAL)
    except InsufficientCreditsError:
        await message.answer(CREDITS_EXCEEDED_TEXT, reply_markup=main_menu_keyboard())
        return
    except QuotaExceededError:
        await message.answer(
            "⚠️ Лимит тарифа исчерпан",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(GENERATION_ACCEPTED_TEXT)
