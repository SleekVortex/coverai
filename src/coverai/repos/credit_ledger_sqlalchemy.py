from typing import cast

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.credit_transaction import CreditTransaction
from coverai.domain.enums import CreditTransactionType
from coverai.infra.db import models


class CreditLedgerSqlAlchemyRepo:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record_transaction(
        self,
        transaction: CreditTransaction,
    ) -> CreditTransaction:
        """Записывает транзакцию кредитов."""
        row = models.CreditTransaction(
            user_id=transaction.user_id,
            type=transaction.type.value,
            amount=transaction.amount,
            balance_after=transaction.balance_after,
            description=transaction.description,
            generation_request_id=transaction.generation_request_id,
            payment_intent_id=transaction.payment_intent_id,
            promo_code_id=transaction.promo_code_id,
            metadata_json=transaction.metadata_json,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return credit_transaction_from_model(row)

    async def grant_welcome_bonus(
        self,
        user_id: int,
        amount: int,
        description: str,
    ) -> CreditTransaction:
        """Начисляет приветственный бонус."""
        user = await self._session.scalar(
            select(models.User).where(models.User.id == user_id).with_for_update(),
        )
        if user is None:
            raise LookupError("user not found")

        user.credits += amount
        row = models.CreditTransaction(
            user_id=user.id,
            type=CreditTransactionType.WELCOME_BONUS.value,
            amount=amount,
            balance_after=user.credits,
            description=description,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return credit_transaction_from_model(row)


def credit_transaction_from_model(row: models.CreditTransaction) -> CreditTransaction:
    """Преобразует модель транзакции."""
    return CreditTransaction(
        id=row.id,
        user_id=row.user_id,
        type=CreditTransactionType(row.type),
        amount=row.amount,
        balance_after=row.balance_after,
        description=row.description,
        generation_request_id=row.generation_request_id,
        payment_intent_id=row.payment_intent_id,
        promo_code_id=row.promo_code_id,
        metadata_json=cast("dict[str, object] | None", row.metadata_json),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
