from coverai.bot.messages import TELEGRAM_USER_MISSING_TEXT
from coverai.bot.protocols import BotUseCases, IncomingMessage
from coverai.domain.entities import User


async def ensure_user(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> User | None:
    """Гарантирует наличие пользователя."""
    if message.from_user is None:
        await message.answer(TELEGRAM_USER_MISSING_TEXT)
        return None

    return await use_cases.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code,
    )
