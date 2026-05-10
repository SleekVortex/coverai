from datetime import UTC, datetime
from uuid import uuid4

from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.credit_transaction import CreditTransaction
from coverai.domain.entities import User
from coverai.domain.enums import CreditTransactionType, PaymentStatus
from coverai.domain.ids import required_id
from coverai.domain.payments import PaymentIntent
from coverai.domain.ports import PaymentRepo, UserRepo
from coverai.services.billing.errors import (
    PaymentNotFoundError,
    PaymentNotRefundableError,
    UserBalanceCannotBeNegativeError,
)
from coverai.services.users.errors import UserNotFoundError


class PaymentService:
    def __init__(
        self,
        payment_repo: PaymentRepo,
        user_repo: UserRepo,
        credit_ledger_repo: CreditLedgerRepo,
        credit_price_rub: int,
    ) -> None:
        self._payment_repo = payment_repo
        self._user_repo = user_repo
        self._credit_ledger_repo = credit_ledger_repo
        self._credit_price_rub = credit_price_rub

    async def create_top_up(
        self,
        user: User,
        credits_amount: int,
        now: datetime | None = None,
    ) -> PaymentIntent:
        """Создает mock-платеж пополнения."""
        user_id = required_id(user)
        current_time = now or datetime.now(UTC)
        discount = user.pending_top_up_discount_percent
        if _discount_expired(user.pending_top_up_discount_valid_until, current_time):
            await self._user_repo.update_pending_top_up_discount(
                user_id=user_id,
                percent=0,
                valid_until=None,
                promo_code_id=None,
            )
            discount = 0

        amount = credits_amount * self._credit_price_rub
        return await self._payment_repo.create(
            PaymentIntent(
                user_id=user_id,
                credits_amount=credits_amount,
                amount_rub=amount * (100 - discount) // 100,
                discount_percent=discount,
                status=PaymentStatus.PENDING,
                provider="mock",
                external_id=f"mock_{uuid4().hex}",
            ),
        )

    async def confirm(self, external_id: str) -> PaymentIntent:
        """Подтверждает платеж."""
        intent = await self._payment_by_external_id(external_id)
        if intent.status == PaymentStatus.SUCCEEDED:
            return intent
        if intent.status != PaymentStatus.PENDING:
            return intent

        user = await self._locked_user(intent.user_id)
        updated = await self._user_repo.update_credits(
            user_id=required_id(user),
            credits=user.credits + intent.credits_amount,
        )
        if updated is None:
            raise UserNotFoundError

        await self._user_repo.update_pending_top_up_discount(
            user_id=required_id(user),
            percent=0,
            valid_until=None,
            promo_code_id=None,
        )
        await self._credit_ledger_repo.record_transaction(
            CreditTransaction(
                user_id=required_id(user),
                type=CreditTransactionType.TOP_UP,
                amount=intent.credits_amount,
                balance_after=updated.credits,
                description="Mock payment top-up",
                payment_intent_id=required_id(intent),
            ),
        )
        confirmed = await self._payment_repo.update_status(
            payment_id=required_id(intent),
            status=PaymentStatus.SUCCEEDED,
            confirmed_at=datetime.now(UTC),
        )
        if confirmed is None:
            raise PaymentNotFoundError
        return confirmed

    async def fail(self, external_id: str) -> PaymentIntent:
        """Помечает платеж ошибочным."""
        return await self._terminal_update(external_id, PaymentStatus.FAILED)

    async def cancel(self, external_id: str) -> PaymentIntent:
        """Отменяет платеж."""
        return await self._terminal_update(external_id, PaymentStatus.CANCELED)

    async def refund(self, payment_id: int) -> PaymentIntent:
        """Возвращает платеж."""
        intent = await self._payment_repo.get_by_id(payment_id)
        if intent is None:
            raise PaymentNotFoundError
        if intent.status not in {
            PaymentStatus.SUCCEEDED,
            PaymentStatus.REFUNDED,
            PaymentStatus.REFUND_MANUAL_REVIEW,
        }:
            raise PaymentNotRefundableError
        if intent.status != PaymentStatus.SUCCEEDED:
            return intent

        user = await self._locked_user(intent.user_id)
        if user.credits < intent.credits_amount:
            updated = await self._payment_repo.update_status(
                payment_id=payment_id,
                status=PaymentStatus.REFUND_MANUAL_REVIEW,
                confirmed_at=datetime.now(UTC),
            )
            if updated is None:
                raise PaymentNotFoundError
            return updated

        updated_user = await self._user_repo.update_credits(
            user_id=required_id(user),
            credits=user.credits - intent.credits_amount,
        )
        if updated_user is None:
            raise UserNotFoundError
        if updated_user.credits < 0:
            raise UserBalanceCannotBeNegativeError

        await self._credit_ledger_repo.record_transaction(
            CreditTransaction(
                user_id=required_id(user),
                type=CreditTransactionType.REFUND,
                amount=-intent.credits_amount,
                balance_after=updated_user.credits,
                description="Mock payment refund",
                payment_intent_id=payment_id,
            ),
        )
        updated = await self._payment_repo.update_status(
            payment_id=payment_id,
            status=PaymentStatus.REFUNDED,
            confirmed_at=datetime.now(UTC),
        )
        if updated is None:
            raise PaymentNotFoundError
        return updated

    async def _terminal_update(
        self,
        external_id: str,
        status: PaymentStatus,
    ) -> PaymentIntent:
        intent = await self._payment_by_external_id(external_id)
        if intent.status != PaymentStatus.PENDING:
            return intent

        updated = await self._payment_repo.update_status(
            payment_id=required_id(intent),
            status=status,
            confirmed_at=datetime.now(UTC),
        )
        if updated is None:
            raise PaymentNotFoundError
        return updated

    async def _payment_by_external_id(self, external_id: str) -> PaymentIntent:
        intent = await self._payment_repo.get_by_external_id(external_id)
        if intent is None:
            raise PaymentNotFoundError
        return intent

    async def _locked_user(self, user_id: int) -> User:
        user = await self._user_repo.get_by_id_for_update(user_id)
        if user is None:
            raise UserNotFoundError
        return user


def _discount_expired(valid_until: datetime | None, now: datetime) -> bool:
    if valid_until is None:
        return False
    if valid_until.tzinfo is None:
        valid_until = valid_until.replace(tzinfo=UTC)
    return valid_until <= now
