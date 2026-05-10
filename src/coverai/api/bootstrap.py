from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from coverai.api.helpers.email import normalize_email
from coverai.configs import Settings
from coverai.domain.enums import Plan, UserRole
from coverai.infra.db import models
from coverai.services.auth import hash_password


async def ensure_admin_user(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> None:
    """Создает администратора при необходимости."""
    async with session_factory() as session, session.begin():
        email = normalize_email(settings.admin.email)
        existing = await session.scalar(
            select(models.User).where(models.User.email == email),
        )
        if existing is not None:
            return

        session.add(
            models.User(
                email=email,
                password_hash=hash_password(settings.admin.password),
                role=UserRole.ADMIN.value,
                plan=Plan.PRO.value,
                credits=100,
            ),
        )
