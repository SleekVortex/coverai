from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest
from fakes.repos import FakeCreditLedgerRepo, FakeUserRepo, id_of

from coverai.domain.entities import User
from coverai.domain.enums import PromoCodeType
from coverai.domain.promocodes import PromoCode
from coverai.services.billing.errors import (
    PromoCodeActivationLimitReachedError,
    PromoCodeExpiredError,
    PromoCodeInactiveError,
)
from coverai.services.billing.promo_service import PromoService


async def test_redeem_inactive_promo_raises_inactive_error() -> None:
    await assert_redeem_raises(
        PromoCode(
            id=1,
            code="TEST",
            type=PromoCodeType.FIXED_CREDITS,
            value=10,
            valid_until=future(),
            max_activations=1,
            is_active=False,
        ),
        PromoCodeInactiveError,
    )


async def test_redeem_expired_promo_raises_expired_error() -> None:
    await assert_redeem_raises(
        PromoCode(
            id=1,
            code="TEST",
            type=PromoCodeType.FIXED_CREDITS,
            value=10,
            valid_until=datetime.now(UTC) - timedelta(seconds=1),
            max_activations=1,
        ),
        PromoCodeExpiredError,
    )


async def test_redeem_promo_at_activations_cap_raises_limit_error() -> None:
    await assert_redeem_raises(
        PromoCode(
            id=1,
            code="TEST",
            type=PromoCodeType.FIXED_CREDITS,
            value=10,
            valid_until=future(),
            max_activations=2,
            activations_count=2,
        ),
        PromoCodeActivationLimitReachedError,
    )


async def assert_redeem_raises(
    promo: PromoCode,
    error_type: type[Exception],
) -> None:
    user_repo = FakeUserRepo()
    service = PromoService(
        promo_repo=FakePromoRepo(promo),
        user_repo=user_repo,
        credit_ledger_repo=FakeCreditLedgerRepo(user_repo),
    )

    with pytest.raises(error_type):
        await service.redeem(User(id=1, telegram_id=None), "test")


def future() -> datetime:
    return datetime.now(UTC) + timedelta(days=1)


class FakePromoRepo:
    def __init__(self, promo: PromoCode) -> None:
        self._promo = promo

    async def create(self, promo: PromoCode) -> PromoCode:
        return promo

    async def get_by_code(self, code: str) -> PromoCode | None:
        if self._promo.code == code:
            return self._promo
        return None

    async def get_by_code_for_update(self, code: str) -> PromoCode | None:
        return await self.get_by_code(code)

    async def was_redeemed(self, _promo_id: int, _user_id: int) -> bool:
        return False

    async def create_redemption(self, _promo_id: int, _user_id: int) -> None:
        return None

    async def increment_activations(self, promo_id: int) -> PromoCode | None:
        if id_of(self._promo) != promo_id:
            return None

        self._promo = replace(
            self._promo,
            activations_count=self._promo.activations_count + 1,
        )
        return self._promo
