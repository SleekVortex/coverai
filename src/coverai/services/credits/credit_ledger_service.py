from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.credit_transaction import CreditTransaction
from coverai.services.config import SERVICE_CONFIG

WELCOME_BONUS_DESCRIPTION = SERVICE_CONFIG.credits.welcome_bonus_description


class CreditLedgerService:
    def __init__(self, credit_ledger_repo: CreditLedgerRepo) -> None:
        self._credit_ledger_repo = credit_ledger_repo

    async def grant_welcome_bonus(
        self,
        user_id: int,
        amount: int,
    ) -> CreditTransaction:
        """Начисляет приветственный бонус."""
        if amount <= 0:
            raise ValueError("welcome bonus amount must be positive")

        return await self._credit_ledger_repo.grant_welcome_bonus(
            user_id=user_id,
            amount=amount,
            description=WELCOME_BONUS_DESCRIPTION,
        )
