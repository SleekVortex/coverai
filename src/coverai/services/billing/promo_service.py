from datetime import UTC, datetime

from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.credit_transaction import CreditTransaction
from coverai.domain.entities import User
from coverai.domain.enums import CreditTransactionType, PromoCodeType
from coverai.domain.ids import required_id
from coverai.domain.ports import PromoCodeRepo, UserRepo
from coverai.domain.promocodes import PromoCode
from coverai.services.billing.errors import (
    PromoCodeActivationLimitReachedError,
    PromoCodeAlreadyExistsError,
    PromoCodeAlreadyRedeemedError,
    PromoCodeExpiredError,
    PromoCodeInactiveError,
    PromoCodeNotFoundError,
)
from coverai.services.billing.models import PromoRedemptionResult
from coverai.services.users.errors import UserNotFoundError


class PromoService:
    def __init__(
        self,
        promo_repo: PromoCodeRepo,
        user_repo: UserRepo,
        credit_ledger_repo: CreditLedgerRepo,
    ) -> None:
        self._promo_repo = promo_repo
        self._user_repo = user_repo
        self._credit_ledger_repo = credit_ledger_repo

    async def create_promo(
        self,
        code: str,
        type: PromoCodeType,
        value: int,
        valid_until: datetime,
        max_activations: int,
    ) -> PromoCode:
        """Создает промокод."""
        normalized = _normalize_code(code)
        if await self._promo_repo.get_by_code(normalized) is not None:
            raise PromoCodeAlreadyExistsError

        return await self._promo_repo.create(
            PromoCode(
                code=normalized,
                type=type,
                value=value,
                valid_until=valid_until,
                max_activations=max_activations,
            ),
        )

    async def redeem(self, user: User, code: str) -> PromoRedemptionResult:
        """Активирует промокод."""
        user_id = required_id(user)
        promo = await self._promo_repo.get_by_code_for_update(_normalize_code(code))
        if promo is None:
            raise PromoCodeNotFoundError
        if await self._promo_repo.was_redeemed(required_id(promo), user_id):
            raise PromoCodeAlreadyRedeemedError
        _validate_promo(promo)

        locked = await self._user_repo.get_by_id_for_update(user_id)
        if locked is None:
            raise UserNotFoundError

        await self._promo_repo.increment_activations(required_id(promo))
        await self._promo_repo.create_redemption(required_id(promo), user_id)
        if promo.type == PromoCodeType.FIXED_CREDITS:
            updated = await self._user_repo.update_credits(
                user_id=user_id,
                credits=locked.credits + promo.value,
            )
            if updated is None:
                raise UserNotFoundError
            await self._credit_ledger_repo.record_transaction(
                CreditTransaction(
                    user_id=user_id,
                    type=CreditTransactionType.PROMO,
                    amount=promo.value,
                    balance_after=updated.credits,
                    description=f"Promo code {promo.code}",
                    promo_code_id=required_id(promo),
                ),
            )
            return PromoRedemptionResult(
                promo=promo,
                message=f"Added {promo.value} credits",
            )

        await self._user_repo.update_pending_top_up_discount(
            user_id=user_id,
            percent=promo.value,
            valid_until=promo.valid_until,
            promo_code_id=required_id(promo),
        )
        return PromoRedemptionResult(
            promo=promo,
            message=f"Next top-up discount is {promo.value}%",
        )


def _normalize_code(code: str) -> str:
    return code.strip().upper()


def _validate_promo(promo: PromoCode) -> None:
    now = datetime.now(UTC)
    valid_until = promo.valid_until
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=UTC)
    if not promo.is_active:
        raise PromoCodeInactiveError
    if valid_until < now:
        raise PromoCodeExpiredError
    if promo.activations_count >= promo.max_activations:
        raise PromoCodeActivationLimitReachedError
