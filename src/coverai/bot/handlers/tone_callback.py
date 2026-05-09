from coverai.bot.helpers.ids import required_id
from coverai.bot.messages import GENERATION_ACCEPTED_TEXT
from coverai.bot.parsing.callback import tone_from_callback
from coverai.bot.protocols import BotUseCases, IncomingCallback
from coverai.bot.state.pending_tone_store import PendingToneStore
from coverai.services.billing.errors import InsufficientCreditsError, QuotaExceededError


async def handle_tone_callback(
    callback: IncomingCallback,
    use_cases: BotUseCases,
    pending_tones: PendingToneStore,
) -> None:
    """Обрабатывает выбор тона."""
    user = await use_cases.get_or_create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name,
        language_code=callback.from_user.language_code,
    )
    user_id = required_id(user)
    vacancy_url = pending_tones.pop(user_id)
    if vacancy_url is None:
        await callback.answer("🔗 Отправьте ссылку заново.", show_alert=True)
        return

    tone = tone_from_callback(callback.data)
    try:
        await use_cases.enqueue_generation(user_id, vacancy_url, tone)
    except InsufficientCreditsError:
        await callback.answer("⚠️ Недостаточно кредитов.", show_alert=True)
        return
    except QuotaExceededError:
        await callback.answer("⚠️ Лимит тарифа исчерпан.", show_alert=True)
        return

    await callback.answer("✅ Генерация в очереди.")
    if callback.message is not None:
        await callback.message.answer(GENERATION_ACCEPTED_TEXT)
