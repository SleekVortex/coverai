from arq import create_pool
from dishka import AsyncContainer
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from coverai.api.bootstrap import ensure_admin_user
from coverai.configs import Settings
from coverai.infra.db.session import create_engine, create_session_factory
from coverai.infra.logging import configure_logging
from coverai.workers.settings import redis_settings_from_url


async def run_startup(app: FastAPI, settings: Settings) -> None:
    """Выполняет startup приложения."""
    configure_logging(settings.app.log_level)
    if app.state.session_factory is None:
        engine = create_engine(settings.database.url)
        app.state.engine = engine
        app.state.session_factory = create_session_factory(engine)
    if app.state.arq_pool is None:
        app.state.arq_pool = await create_pool(
            redis_settings_from_url(settings.redis.url),
        )
    await ensure_admin_user(app.state.session_factory, settings)


async def run_shutdown(app: FastAPI) -> None:
    """Выполняет shutdown приложения."""
    pool = app.state.arq_pool
    if pool is not None and not app.state.external_arq_pool:
        await pool.aclose()
    engine = app.state.engine
    if isinstance(engine, AsyncEngine):
        await engine.dispose()
    container = app.state.dishka_container
    if isinstance(container, AsyncContainer):
        await container.close()
