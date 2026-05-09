from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from coverai.configs import get_settings


def create_engine(database_url: str | None = None) -> AsyncEngine:
    """Создает SQLAlchemy engine."""
    return create_async_engine(database_url or get_settings().database.url)


def create_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Создает фабрику сессий."""
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    """Открывает транзакционную сессию."""
    async with session_factory() as session, session.begin():
        yield session
