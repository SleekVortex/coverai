from arq.connections import ArqRedis
from fastapi import FastAPI
from prometheus_client import make_asgi_app
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from coverai.api.bootstrap import ensure_admin_user
from coverai.api.lifespan import run_shutdown, run_startup
from coverai.api.routes import ROUTERS
from coverai.configs import Settings, get_settings
from coverai.di.container import create_di_container

__all__ = ["app", "create_app", "ensure_admin_user"]


def create_app(
    settings: Settings | None = None,
    session_factory: async_sessionmaker[AsyncSession] | None = None,
    arq_pool: ArqRedis | None = None,
) -> FastAPI:
    """Создает FastAPI-приложение."""
    app_settings = settings or get_settings()
    app = FastAPI(
        title="CoverAI LLM API",
        description="REST API for asynchronous LLM cover letter generation.",
        version="0.1.0",
    )
    app.state.settings = app_settings
    app.state.external_session_factory = session_factory
    app.state.session_factory = session_factory
    app.state.engine = None
    app.state.external_arq_pool = arq_pool
    app.state.arq_pool = arq_pool
    app.state.dishka_container = create_di_container(app_settings)

    @app.on_event("startup")
    async def startup() -> None:
        await run_startup(app, app_settings)

    @app.on_event("shutdown")
    async def shutdown() -> None:
        await run_shutdown(app)

    app.mount("/metrics", make_asgi_app())
    for router in ROUTERS:
        app.include_router(router)

    return app


app = create_app()
