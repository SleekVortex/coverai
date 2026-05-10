from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.enums import PromoCodeType
from coverai.domain.promocodes import PromoCode
from coverai.infra.db import models


class PromoCodeSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, promo: PromoCode) -> PromoCode:
        """Создает промокод."""
        row = models.PromoCode(
            code=promo.code,
            type=promo.type.value,
            value=promo.value,
            valid_until=promo.valid_until,
            max_activations=promo.max_activations,
            activations_count=promo.activations_count,
            is_active=promo.is_active,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return promo_from_model(row)

    async def get_by_code(self, code: str) -> PromoCode | None:
        """Возвращает промокод по коду."""
        row = await self._session.scalar(
            select(models.PromoCode).where(models.PromoCode.code == code),
        )
        return promo_from_model(row) if row else None

    async def get_by_code_for_update(self, code: str) -> PromoCode | None:
        """Возвращает промокод по коду с блокировкой."""
        row = await self._session.scalar(
            select(models.PromoCode)
            .where(models.PromoCode.code == code)
            .with_for_update(),
        )
        return promo_from_model(row) if row else None

    async def was_redeemed(self, promo_id: int, user_id: int) -> bool:
        """Проверяет, был ли промокод активирован пользователем."""
        existing = await self._session.scalar(
            select(models.PromoRedemption).where(
                models.PromoRedemption.promo_code_id == promo_id,
                models.PromoRedemption.user_id == user_id,
            ),
        )
        return existing is not None

    async def create_redemption(self, promo_id: int, user_id: int) -> None:
        """Создает запись активации промокода."""
        self._session.add(
            models.PromoRedemption(promo_code_id=promo_id, user_id=user_id),
        )
        await self._session.flush()

    async def increment_activations(self, promo_id: int) -> PromoCode | None:
        """Увеличивает счетчик активаций."""
        row = await self._session.get(models.PromoCode, promo_id)
        if row is None:
            return None

        row.activations_count += 1
        await self._session.flush()
        await self._session.refresh(row)
        return promo_from_model(row)


def promo_from_model(row: models.PromoCode) -> PromoCode:
    """Преобразует модель промокода."""
    return PromoCode(
        id=row.id,
        code=row.code,
        type=PromoCodeType(row.type),
        value=row.value,
        valid_until=row.valid_until,
        max_activations=row.max_activations,
        activations_count=row.activations_count,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )

