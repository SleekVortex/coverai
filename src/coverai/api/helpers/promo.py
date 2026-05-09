from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.infra.db import models


async def promo_by_code(session: AsyncSession, code: str) -> models.PromoCode | None:
    """Возвращает промокод по коду."""
    return await session.scalar(
        select(models.PromoCode)
        .where(models.PromoCode.code == code.strip().upper())
        .with_for_update(),
    )


async def promo_was_redeemed(
    session: AsyncSession,
    promo_id: int,
    user_id: int,
) -> bool:
    """Проверяет активацию промокода."""
    redemption = await session.scalar(
        select(models.PromoRedemption).where(
            models.PromoRedemption.promo_code_id == promo_id,
            models.PromoRedemption.user_id == user_id,
        ),
    )
    return redemption is not None


def validate_promo(promo: models.PromoCode) -> None:
    """Проверяет доступность промокода."""
    if not promo.is_active:
        raise HTTPException(status_code=400, detail="Promo code is inactive")
    valid_until = promo.valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=UTC)
    if valid_until < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Promo code expired")
    if promo.activations_count >= promo.max_activations:
        raise HTTPException(
            status_code=400,
            detail="Promo code activation limit reached",
        )
