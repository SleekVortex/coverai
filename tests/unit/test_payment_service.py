from dataclasses import replace
from datetime import UTC, datetime

from fakes.repos import FakeCreditLedgerRepo, FakeUserRepo, id_of

from coverai.domain.entities import User
from coverai.domain.enums import PaymentStatus
from coverai.domain.payments import PaymentIntent
from coverai.services.billing import PaymentService


async def test_confirm_is_idempotent_for_successful_payment() -> None:
    user_repo = FakeUserRepo()
    user = await user_repo.create(User(id=None, telegram_id=None, credits=5))
    payment_repo = FakePaymentRepo()
    ledger_repo = FakeCreditLedgerRepo(user_repo)
    intent = await payment_repo.create(
        PaymentIntent(
            user_id=id_of(user),
            credits_amount=10,
            amount_rub=10,
            discount_percent=0,
            status=PaymentStatus.PENDING,
            provider="mock",
            external_id="payment-1",
        ),
    )
    service = PaymentService(
        payment_repo=payment_repo,
        user_repo=user_repo,
        credit_ledger_repo=ledger_repo,
        credit_price_rub=1,
    )

    first = await service.confirm(intent.external_id)
    second = await service.confirm(intent.external_id)

    assert first.status == PaymentStatus.SUCCEEDED
    assert second.status == PaymentStatus.SUCCEEDED
    assert user_repo.users[id_of(user)].credits == 15
    assert len(ledger_repo.transactions) == 1


class FakePaymentRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.intents: dict[int, PaymentIntent] = {}

    async def create(self, intent: PaymentIntent) -> PaymentIntent:
        created = replace(
            intent,
            id=self._next(),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        self.intents[id_of(created)] = created
        return created

    async def get_by_id(self, payment_id: int) -> PaymentIntent | None:
        return self.intents.get(payment_id)

    async def get_by_external_id(self, external_id: str) -> PaymentIntent | None:
        return next(
            (
                intent
                for intent in self.intents.values()
                if intent.external_id == external_id
            ),
            None,
        )

    async def update_status(
        self,
        payment_id: int,
        status: PaymentStatus,
        confirmed_at: datetime | None = None,
    ) -> PaymentIntent | None:
        intent = self.intents.get(payment_id)
        if intent is None:
            return None

        updated = replace(
            intent,
            status=status,
            confirmed_at=confirmed_at,
            updated_at=datetime.now(UTC),
        )
        self.intents[payment_id] = updated
        return updated

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value
