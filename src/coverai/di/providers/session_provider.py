from dishka import Provider, Scope, from_context
from sqlalchemy.ext.asyncio import AsyncSession


class SessionProvider(Provider):
    session = from_context(AsyncSession, scope=Scope.REQUEST)
