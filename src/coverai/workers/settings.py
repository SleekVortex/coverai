from collections.abc import Awaitable, Callable
from typing import ClassVar
from urllib.parse import urlparse

from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import AsyncEngine

from coverai.configs import get_settings
from coverai.infra.db.session import create_engine, create_session_factory
from coverai.infra.logging import configure_logging
from coverai.infra.metrics import prometheus_metrics, start_metrics_server
from coverai.workers.tasks import generate_cover_letter


def redis_settings_from_url(redis_url: str) -> RedisSettings:
    """Создает настройки Redis из URL."""
    parsed = urlparse(redis_url)
    database = parsed.path.removeprefix("/") or "0"

    return RedisSettings(
        host=parsed.hostname or "redis",
        port=parsed.port or 6379,
        database=int(database),
        username=parsed.username,
        password=parsed.password,
    )


async def startup(ctx: dict[str, object]) -> None:
    """Инициализирует worker."""
    settings = get_settings()
    configure_logging(settings.app.log_level)

    if settings.metrics.enabled:
        start_metrics_server(settings.metrics.worker_port)
        prometheus_metrics.set_arq_queue_size("default", 0)

    engine = create_engine(settings.database.url)
    ctx["settings"] = settings
    ctx["engine"] = engine
    ctx["session_factory"] = create_session_factory(engine)


async def shutdown(ctx: dict[str, object]) -> None:
    """Завершает worker."""
    engine = ctx.get("engine")
    if isinstance(engine, AsyncEngine):
        await engine.dispose()


class WorkerSettings:
    """arq worker settings."""

    functions: ClassVar[list[object]] = [generate_cover_letter]
    on_startup: ClassVar[Callable[[dict[str, object]], Awaitable[None]]] = startup
    on_shutdown: ClassVar[Callable[[dict[str, object]], Awaitable[None]]] = shutdown
    redis_settings: ClassVar[RedisSettings] = redis_settings_from_url(
        get_settings().redis.url,
    )
