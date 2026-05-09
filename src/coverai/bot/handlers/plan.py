from coverai.bot.formatters.credits import format_credit_balance
from coverai.bot.helpers.ids import required_id
from coverai.bot.helpers.users import ensure_user
from coverai.bot.protocols import BotUseCases, IncomingMessage


async def handle_plan_command(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> None:
    """Обрабатывает команду баланса."""
    user = await ensure_user(message, use_cases)
    if user is None:
        return

    credits = await use_cases.get_credit_balance(required_id(user))
    await message.answer(format_credit_balance(credits))
