from typing import Protocol, runtime_checkable

from coverai.domain.credit_transaction import CreditTransaction


@runtime_checkable
class CreditLedgerRepo(Protocol):
    async def grant_welcome_bonus(
        self,
        user_id: int,
        amount: int,
        description: str,
    ) -> CreditTransaction:
        """Начисляет приветственный бонус."""
        ...
