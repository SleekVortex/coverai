from coverai.bot.formatters.profile import format_profile
from coverai.bot.helpers.ids import required_id
from coverai.bot.helpers.users import ensure_user
from coverai.bot.keyboards.main_menu import main_menu_keyboard
from coverai.bot.messages import PROFILE_MISSING_TEXT
from coverai.bot.protocols import BotUseCases, IncomingMessage
from coverai.services.profile.errors import ProfileNotFoundError


async def handle_profile_command(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> None:
    """Обрабатывает команду профиля."""
    user = await ensure_user(message, use_cases)
    if user is None:
        return

    try:
        profile = await use_cases.get_profile(required_id(user))
    except ProfileNotFoundError:
        await message.answer(PROFILE_MISSING_TEXT, reply_markup=main_menu_keyboard())
        return

    await message.answer(format_profile(profile))
