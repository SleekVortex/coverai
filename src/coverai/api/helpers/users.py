from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.infra.db import models


async def user_by_email(session: AsyncSession, email: str) -> models.User | None:
    """Возвращает пользователя по email."""
    return await session.scalar(select(models.User).where(models.User.email == email))


async def locked_user(session: AsyncSession, user_id: int) -> models.User:
    """Возвращает пользователя с блокировкой."""
    user = await session.scalar(
        select(models.User).where(models.User.id == user_id).with_for_update(),
    )
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
