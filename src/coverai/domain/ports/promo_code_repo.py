from typing import Protocol, runtime_checkable

from coverai.domain.promocodes import PromoCode


@runtime_checkable
class PromoCodeRepo(Protocol):
    async def create(self, promo: PromoCode) -> PromoCode:
        """Создает промокод."""
        ...

    async def get_by_code(self, code: str) -> PromoCode | None:
        """Возвращает промокод по коду."""
        ...

    async def get_by_code_for_update(self, code: str) -> PromoCode | None:
        """Возвращает промокод по коду с блокировкой."""
        ...

    async def was_redeemed(self, promo_id: int, user_id: int) -> bool:
        """Проверяет, был ли промокод активирован пользователем."""
        ...

    async def create_redemption(self, promo_id: int, user_id: int) -> None:
        """Создает запись активации промокода."""
        ...

    async def increment_activations(self, promo_id: int) -> PromoCode | None:
        """Увеличивает счетчик активаций."""
        ...

