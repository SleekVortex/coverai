import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from arq import create_pool

from coverai.bot.handlers import PendingToneStore, create_router
from coverai.bot.runtime import RuntimeBotUseCases
from coverai.configs import get_settings
from coverai.infra.db.session import create_engine, create_session_factory
from coverai.infra.logging import configure_logging
from coverai.infra.metrics import start_metrics_server
from coverai.workers.settings import redis_settings_from_url


async def amain() -> None:
    """Запускает приложение асинхронно."""
    settings = get_settings()
    configure_logging(settings.app.log_level)

    if settings.metrics.enabled:
        start_metrics_server(settings.metrics.bot_port)

    if not settings.telegram.bot_token:
        await asyncio.Event().wait()
        return

    engine = create_engine(settings.database.url)
    session_factory = create_session_factory(engine)
    telegram_session = None
    if settings.telegram.proxy_url:
        telegram_session = AiohttpSession(proxy=settings.telegram.proxy_url)

    bot = Bot(settings.telegram.bot_token, session=telegram_session)
    arq_pool = await create_pool(redis_settings_from_url(settings.redis.url))
    dispatcher = Dispatcher()
    use_cases = RuntimeBotUseCases(
        bot=bot,
        session_factory=session_factory,
        arq_pool=arq_pool,
    )
    dispatcher.include_router(create_router(use_cases, PendingToneStore()))

    try:
        await dispatcher.start_polling(bot)
    finally:
        await use_cases.aclose()
        await arq_pool.aclose()
        await bot.session.close()
        await engine.dispose()


def main() -> None:
    """Запускает приложение."""
    asyncio.run(amain())


if __name__ == "__main__":
    main()
