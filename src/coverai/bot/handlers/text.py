from coverai.bot.formatters.profile import format_profile_saved
from coverai.bot.handlers.generation import handle_vacancy_url
from coverai.bot.handlers.history import handle_history_command
from coverai.bot.handlers.plan import handle_plan_command
from coverai.bot.handlers.profile import handle_profile_command
from coverai.bot.helpers.ids import required_id
from coverai.bot.helpers.users import ensure_user
from coverai.bot.keyboards.main_menu import (
    MAIN_MENU_HELP,
    MAIN_MENU_HISTORY,
    MAIN_MENU_PLAN,
    MAIN_MENU_PROFILE,
    MAIN_MENU_SUBSCRIBE,
    main_menu_keyboard,
)
from coverai.bot.messages import (
    HELP_TEXT,
    MULTIPLE_VACANCY_URLS_TEXT,
    RESUME_TEXT_TOO_SHORT_TEXT,
    SUBSCRIBE_TEXT,
)
from coverai.bot.protocols import BotUseCases, IncomingMessage
from coverai.bot.state.pending_tone_store import PendingToneStore
from coverai.domain.entities import User
from coverai.services.profile.errors import ResumeTextTooShortError
from coverai.services.vacancy import parse_hh_vacancy_id
from coverai.services.vacancy.errors import (
    InvalidVacancyUrlError,
    MultipleVacancyUrlsError,
)


async def handle_text_message(
    message: IncomingMessage,
    use_cases: BotUseCases,
    pending_tones: PendingToneStore,
) -> None:
    """Обрабатывает текстовое сообщение."""
    user = await ensure_user(message, use_cases)
    if user is None or message.text is None:
        return

    if await handle_main_menu_text(message, use_cases):
        return

    try:
        parse_hh_vacancy_id(message.text)
    except MultipleVacancyUrlsError:
        await message.answer(MULTIPLE_VACANCY_URLS_TEXT)
        return
    except InvalidVacancyUrlError:
        await save_resume_from_text(message, use_cases, user)
        return

    await handle_vacancy_url(message, use_cases, pending_tones, user, message.text)


async def handle_main_menu_text(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> bool:
    """Обрабатывает текст главного меню."""
    if message.text in {MAIN_MENU_PROFILE, "Профиль"}:
        await handle_profile_command(message, use_cases)
        return True
    if message.text in {MAIN_MENU_PLAN, "Тариф и лимиты", "Мой лимит", "Баланс"}:
        await handle_plan_command(message, use_cases)
        return True
    if message.text in {MAIN_MENU_HISTORY, "История писем"}:
        await handle_history_command(message, use_cases)
        return True
    if message.text in {MAIN_MENU_SUBSCRIBE, "Тарифы"}:
        await message.answer(SUBSCRIBE_TEXT, reply_markup=main_menu_keyboard())
        return True
    if message.text in {MAIN_MENU_HELP, "Помощь"}:
        await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())
        return True

    return False


async def save_resume_from_text(
    message: IncomingMessage,
    use_cases: BotUseCases,
    user: User,
) -> None:
    """Сохраняет резюме из текста."""
    if message.text is None:
        return

    try:
        result = await use_cases.save_resume_text(
            user_id=required_id(user),
            resume_text=message.text,
        )
    except ResumeTextTooShortError:
        await message.answer(RESUME_TEXT_TOO_SHORT_TEXT)
        return

    await message.answer(format_profile_saved(result))
