from coverai.bot.helpers.users import ensure_user
from coverai.bot.keyboards.main_menu import main_menu_keyboard
from coverai.bot.messages import HELP_TEXT, START_TEXT
from coverai.bot.protocols import BotUseCases, IncomingMessage


async def handle_start(message: IncomingMessage, use_cases: BotUseCases) -> None:
    """Обрабатывает старт бота."""
    await ensure_user(message, use_cases)
    await message.answer(START_TEXT, reply_markup=main_menu_keyboard())


async def handle_help_command(message: IncomingMessage) -> None:
    """Обрабатывает команду помощи."""
    await message.answer(HELP_TEXT, reply_markup=main_menu_keyboard())
