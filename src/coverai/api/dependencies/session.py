from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Открывает сессию базы данных."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session, session.begin():
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]
