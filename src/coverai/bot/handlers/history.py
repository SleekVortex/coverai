from coverai.bot.formatters.history import format_history_detail, format_history_list
from coverai.bot.helpers.ids import required_id
from coverai.bot.helpers.users import ensure_user
from coverai.bot.keyboards.main_menu import main_menu_keyboard
from coverai.bot.messages import HISTORY_LETTER_NOT_FOUND_TEXT, HISTORY_PAYWALL_TEXT
from coverai.bot.parsing.history import history_letter_id
from coverai.bot.protocols import BotUseCases, IncomingMessage
from coverai.services.history.errors import (
    CoverLetterNotFoundError,
    HistoryAccessDeniedError,
)


async def handle_history_command(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> None:
    """Обрабатывает команду истории."""
    user = await ensure_user(message, use_cases)
    if user is None:
        return

    letter_id = history_letter_id(message.text)
    try:
        if letter_id is not None:
            letter = await use_cases.get_history_letter(required_id(user), letter_id)
            await message.answer(format_history_detail(letter))
            return

        history = await use_cases.list_history(required_id(user))
    except HistoryAccessDeniedError:
        await message.answer(HISTORY_PAYWALL_TEXT, reply_markup=main_menu_keyboard())
        return
    except CoverLetterNotFoundError:
        await message.answer(HISTORY_LETTER_NOT_FOUND_TEXT)
        return

    await message.answer(format_history_list(history))
