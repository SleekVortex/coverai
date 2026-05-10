from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.credit_transaction import CreditTransaction
from coverai.domain.enums import CreditTransactionType, Plan, SubscriptionStatus
from coverai.domain.ports import SubscriptionRepo, UserRepo
from coverai.services.billing.errors import UserBalanceCannotBeNegativeError
from coverai.services.users.errors import UserNotFoundError


class AdminCommandService:
    def __init__(
        self,
        user_repo: UserRepo,
        subscription_repo: SubscriptionRepo,
        credit_ledger_repo: CreditLedgerRepo,
    ) -> None:
        self._user_repo = user_repo
        self._subscription_repo = subscription_repo
        self._credit_ledger_repo = credit_ledger_repo

    async def adjust_balance(
        self,
        user_id: int,
        amount: int,
        reason: str,
        admin_id: int,
    ) -> dict[str, int]:
        """Изменяет баланс пользователя."""
        target = await self._user_repo.get_by_id_for_update(user_id)
        if target is None:
            raise UserNotFoundError

        balance = target.credits + amount
        if balance < 0:
            raise UserBalanceCannotBeNegativeError
        updated = await self._user_repo.update_credits(user_id, balance)
        if updated is None:
            raise UserNotFoundError

        await self._credit_ledger_repo.record_transaction(
            CreditTransaction(
                user_id=user_id,
                type=CreditTransactionType.ADJUSTMENT,
                amount=amount,
                balance_after=updated.credits,
                description=reason,
                metadata_json={"reason": reason, "admin_id": admin_id},
            ),
        )
        return {"user_id": user_id, "balance_credits": updated.credits}

    async def expire_subscription(self, user_id: int) -> dict[str, str | int]:
        """Завершает подписку пользователя."""
        target = await self._user_repo.get_by_id(user_id)
        if target is None:
            raise UserNotFoundError

        subscription = await self._subscription_repo.get_active_by_user_id(user_id)
        if subscription is not None and subscription.id is not None:
            await self._subscription_repo.update_status(
                subscription.id,
                SubscriptionStatus.EXPIRED,
            )
        updated = await self._user_repo.update_plan(user_id, Plan.FREE)
        if updated is None:
            raise UserNotFoundError
        return {
            "user_id": user_id,
            "plan": updated.plan.value,
            "subscription_status": "expired",
        }

