from typing import cast

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery
from aiogram.types import Message as AiogramMessage

from coverai.bot.handlers.billing import (
    handle_redeem_command,
    handle_subscribe_command,
    handle_topup_command,
)
from coverai.bot.handlers.document import handle_document
from coverai.bot.handlers.history import handle_history_command
from coverai.bot.handlers.plan import handle_plan_command
from coverai.bot.handlers.profile import handle_profile_command
from coverai.bot.handlers.start import handle_help_command, handle_start
from coverai.bot.handlers.text import handle_text_message
from coverai.bot.handlers.tone_callback import handle_tone_callback
from coverai.bot.protocols import BotUseCases, IncomingCallback, IncomingMessage
from coverai.bot.state.pending_tone_store import PendingToneStore


def create_router(
    use_cases: BotUseCases,
    pending_tones: PendingToneStore | None = None,
) -> Router:
    """Создает router бота."""
    router = Router()
    tone_store = pending_tones or PendingToneStore()

    @router.message(Command("start"))
    async def start(message: AiogramMessage) -> None:
        await handle_start(cast(IncomingMessage, message), use_cases)

    @router.message(Command("profile"))
    async def profile(message: AiogramMessage) -> None:
        await handle_profile_command(cast(IncomingMessage, message), use_cases)

    @router.message(Command("plan"))
    async def plan(message: AiogramMessage) -> None:
        await handle_plan_command(cast(IncomingMessage, message), use_cases)

    @router.message(Command("balance"))
    async def balance(message: AiogramMessage) -> None:
        await handle_plan_command(cast(IncomingMessage, message), use_cases)

    @router.message(Command("redeem"))
    async def redeem(message: AiogramMessage) -> None:
        await handle_redeem_command(cast(IncomingMessage, message), use_cases)

    @router.message(Command("topup"))
    async def topup(message: AiogramMessage) -> None:
        await handle_topup_command(cast(IncomingMessage, message), use_cases)

    @router.message(Command("subscribe"))
    async def subscribe(message: AiogramMessage) -> None:
        await handle_subscribe_command(cast(IncomingMessage, message))

    @router.message(Command("history"))
    async def history(message: AiogramMessage) -> None:
        await handle_history_command(cast(IncomingMessage, message), use_cases)

    @router.message(Command("help"))
    async def help_command(message: AiogramMessage) -> None:
        await handle_help_command(cast(IncomingMessage, message))

    @router.message(F.document)
    async def document(message: AiogramMessage) -> None:
        await handle_document(cast(IncomingMessage, message), use_cases)

    @router.message(F.text)
    async def text(message: AiogramMessage) -> None:
        await handle_text_message(cast(IncomingMessage, message), use_cases, tone_store)

    @router.callback_query(F.data.startswith("tone:"))
    async def tone(callback: CallbackQuery) -> None:
        await handle_tone_callback(
            cast(IncomingCallback, callback),
            use_cases,
            tone_store,
        )

    return router
