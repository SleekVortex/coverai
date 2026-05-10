from coverai.bot.helpers.users import ensure_user
from coverai.bot.keyboards.main_menu import main_menu_keyboard
from coverai.bot.messages import SUBSCRIBE_TEXT
from coverai.bot.protocols import BotUseCases, IncomingMessage


async def handle_redeem_command(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> None:
    """Обрабатывает команду промокода."""
    user = await ensure_user(message, use_cases)
    if user is None or message.text is None:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip():
        await message.answer("Введите промокод: /redeem WELCOME100")
        return

    result = await use_cases.redeem_promo_code(user, parts[1])
    await message.answer(result)


async def handle_topup_command(
    message: IncomingMessage,
    use_cases: BotUseCases,
) -> None:
    """Обрабатывает команду пополнения."""
    user = await ensure_user(message, use_cases)
    if user is None or message.text is None:
        return

    parts = message.text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip().isdecimal():
        await message.answer("Введите количество кредитов: /topup 100")
        return

    result = await use_cases.create_mock_top_up(user, int(parts[1]))
    await message.answer(result)


async def handle_subscribe_command(message: IncomingMessage) -> None:
    """Обрабатывает команду подписки."""
    await message.answer(SUBSCRIBE_TEXT, reply_markup=main_menu_keyboard())
