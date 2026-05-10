import pytest
from fakes.repos import FakeCreditLedgerRepo, FakeUserRepo

from coverai.domain.entities import User
from coverai.domain.user_registration_repo import UserRegistrationConflictError
from coverai.services.credits import CreditLedgerService
from coverai.services.users import UserRegistrationService
from coverai.services.users.errors import UserAlreadyExistsError


async def test_register_api_user_translates_repo_conflict_to_already_exists() -> None:
    user_repo = ConflictUserRepo()
    ledger_repo = FakeCreditLedgerRepo(user_repo)
    service = UserRegistrationService(
        user_repo=user_repo,
        credit_ledger_service=CreditLedgerService(ledger_repo),
        welcome_credits=1,
    )

    with pytest.raises(UserAlreadyExistsError):
        await service.register_api_user(
            email="user@example.test",
            password_hash="hash",
        )

    assert ledger_repo.transactions == {}


class ConflictUserRepo(FakeUserRepo):
    async def create(self, _user: User) -> User:
        raise UserRegistrationConflictError
