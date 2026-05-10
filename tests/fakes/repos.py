from dataclasses import replace
from datetime import UTC, datetime

from coverai.domain.credit_transaction import CreditTransaction
from coverai.domain.entities import (
    CoverLetter,
    Employer,
    GenerationRequest,
    ResumeProfile,
    Subscription,
    User,
    Vacancy,
)
from coverai.domain.enums import (
    CreditTransactionType,
    GenerationStatus,
    Plan,
    SubscriptionStatus,
)


class FakeUserRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.users: dict[int, User] = {}

    async def create(self, user: User) -> User:
        if any(
            user.telegram_id is not None and existing.telegram_id == user.telegram_id
            for existing in self.users.values()
        ):
            raise ValueError("telegram_id already exists")

        created = replace(
            user,
            id=self._next(),
            created_at=now(),
            updated_at=now(),
        )
        self.users[id_of(created)] = created
        return created

    async def get_by_id(self, user_id: int) -> User | None:
        return self.users.get(user_id)

    async def get_by_id_for_update(self, user_id: int) -> User | None:
        return await self.get_by_id(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next(
            (user for user in self.users.values() if user.email == email),
            None,
        )

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return next(
            (user for user in self.users.values() if user.telegram_id == telegram_id),
            None,
        )

    async def update_plan(self, user_id: int, plan: Plan) -> User | None:
        user = self.users.get(user_id)
        if user is None:
            return None

        updated = replace(user, plan=plan, updated_at=now())
        self.users[user_id] = updated
        return updated

    async def update_credits(self, user_id: int, credits: int) -> User | None:
        user = self.users.get(user_id)
        if user is None:
            return None

        updated = replace(user, credits=credits, updated_at=now())
        self.users[user_id] = updated
        return updated

    async def update_pending_top_up_discount(
        self,
        user_id: int,
        percent: int,
        valid_until: datetime | None,
        promo_code_id: int | None,
    ) -> User | None:
        user = self.users.get(user_id)
        if user is None:
            return None

        updated = replace(
            user,
            pending_top_up_discount_percent=percent,
            pending_top_up_discount_valid_until=valid_until,
            pending_top_up_discount_promo_code_id=promo_code_id,
            updated_at=now(),
        )
        self.users[user_id] = updated
        return updated

    async def apply_credit_delta(self, user_id: int, amount: int) -> User | None:
        user = self.users.get(user_id)
        if user is None:
            return None

        updated = replace(user, credits=user.credits + amount, updated_at=now())
        self.users[user_id] = updated
        return updated

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


class FakeCreditLedgerRepo:
    def __init__(self, user_repo: FakeUserRepo) -> None:
        self._next_id = 1
        self._user_repo = user_repo
        self.transactions: dict[int, CreditTransaction] = {}

    async def grant_welcome_bonus(
        self,
        user_id: int,
        amount: int,
        description: str,
    ) -> CreditTransaction:
        user = self._user_repo.users.get(user_id)
        if user is None:
            raise LookupError("user not found")

        updated = replace(user, credits=user.credits + amount, updated_at=now())
        self._user_repo.users[user_id] = updated
        transaction = CreditTransaction(
            id=self._next(),
            user_id=user_id,
            type=CreditTransactionType.WELCOME_BONUS,
            amount=amount,
            balance_after=updated.credits,
            description=description,
            created_at=now(),
            updated_at=now(),
        )
        self.transactions[id_of(transaction)] = transaction
        return transaction

    async def record_transaction(
        self,
        transaction: CreditTransaction,
    ) -> CreditTransaction:
        created = replace(
            transaction,
            id=self._next(),
            created_at=transaction.created_at or now(),
            updated_at=transaction.updated_at or now(),
        )
        self.transactions[id_of(created)] = created
        return created

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


class FakeResumeProfileRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.profiles: dict[int, ResumeProfile] = {}

    async def create(self, profile: ResumeProfile) -> ResumeProfile:
        if any(
            existing.user_id == profile.user_id for existing in self.profiles.values()
        ):
            raise ValueError("profile for user already exists")

        created = replace(
            profile,
            id=self._next(),
            created_at=now(),
            updated_at=now(),
        )
        self.profiles[id_of(created)] = created
        return created

    async def get_by_user_id(self, user_id: int) -> ResumeProfile | None:
        return next(
            (
                profile
                for profile in self.profiles.values()
                if profile.user_id == user_id
            ),
            None,
        )

    async def update_text(
        self,
        profile_id: int,
        resume_text: str,
    ) -> ResumeProfile | None:
        profile = self.profiles.get(profile_id)
        if profile is None:
            return None

        updated = replace(profile, resume_text=resume_text, updated_at=now())
        self.profiles[profile_id] = updated
        return updated

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


class FakeGenerationRequestRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.requests: dict[int, GenerationRequest] = {}

    async def create(self, request: GenerationRequest) -> GenerationRequest:
        created = replace(
            request,
            id=self._next(),
            created_at=request.created_at or now(),
            updated_at=request.updated_at or now(),
        )
        self.requests[id_of(created)] = created
        return created

    async def get_by_id(self, request_id: int) -> GenerationRequest | None:
        return self.requests.get(request_id)

    async def get_by_id_for_user(
        self,
        request_id: int,
        user_id: int,
    ) -> GenerationRequest | None:
        request = self.requests.get(request_id)
        if request is None or request.user_id != user_id:
            return None

        return request

    async def update_status(
        self,
        request_id: int,
        status: GenerationStatus,
        error_message: str | None = None,
        completed_at: datetime | None = None,
    ) -> GenerationRequest | None:
        request = self.requests.get(request_id)
        if request is None:
            return None

        updated = replace(
            request,
            status=status,
            error_message=error_message,
            completed_at=completed_at,
            updated_at=now(),
        )
        self.requests[request_id] = updated
        return updated

    async def count_by_user_statuses_since(
        self,
        user_id: int,
        statuses: set[GenerationStatus],
        since: datetime,
    ) -> int:
        return sum(
            1
            for request in self.requests.values()
            if request.user_id == user_id
            and request.status in statuses
            and request.created_at is not None
            and request.created_at >= since
        )

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


class FakeCoverLetterRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.letters: dict[int, CoverLetter] = {}

    async def create(self, letter: CoverLetter) -> CoverLetter:
        created = replace(
            letter,
            id=self._next(),
            created_at=letter.created_at or now(),
        )
        self.letters[id_of(created)] = created
        return created

    async def get_by_id(self, letter_id: int) -> CoverLetter | None:
        return self.letters.get(letter_id)

    async def list_by_user_id(
        self,
        user_id: int,
        limit: int = 20,
    ) -> list[CoverLetter]:
        return await self.list_by_user_id_since(user_id, since=None, limit=limit)

    async def list_by_user_id_since(
        self,
        user_id: int,
        since: datetime | None,
        limit: int = 20,
    ) -> list[CoverLetter]:
        letters = [
            letter
            for letter in self.letters.values()
            if letter.user_id == user_id
            and (
                since is None
                or letter.created_at is not None
                and letter.created_at >= since
            )
        ]
        return sorted(
            letters,
            key=lambda letter: (
                letter.created_at or datetime.min.replace(tzinfo=UTC),
                id_of(letter),
            ),
            reverse=True,
        )[:limit]

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


class FakeVacancyRepo:
    def __init__(self) -> None:
        self._next_employer_id = 1
        self._next_vacancy_id = 1
        self.employers: dict[int, Employer] = {}
        self.vacancies: dict[int, Vacancy] = {}

    async def create_employer(self, employer: Employer) -> Employer:
        if any(
            existing.hh_id == employer.hh_id for existing in self.employers.values()
        ):
            raise ValueError("employer hh_id already exists")

        created = replace(
            employer,
            id=self._next_employer(),
            created_at=now(),
            updated_at=now(),
        )
        self.employers[id_of(created)] = created
        return created

    async def get_employer_by_hh_id(self, hh_id: int) -> Employer | None:
        return next(
            (
                employer
                for employer in self.employers.values()
                if employer.hh_id == hh_id
            ),
            None,
        )

    async def get_employer_by_id(self, employer_id: int) -> Employer | None:
        return self.employers.get(employer_id)

    async def update_employer_cache(
        self,
        employer_id: int,
        name: str,
        url: str | None,
        raw_payload: dict[str, object] | None,
        cached_at: datetime | None,
    ) -> Employer | None:
        employer = self.employers.get(employer_id)
        if employer is None:
            return None

        updated = replace(
            employer,
            name=name,
            url=url,
            raw_payload=raw_payload,
            cached_at=cached_at,
            updated_at=now(),
        )
        self.employers[employer_id] = updated
        return updated

    async def create_vacancy(self, vacancy: Vacancy) -> Vacancy:
        if any(existing.hh_id == vacancy.hh_id for existing in self.vacancies.values()):
            raise ValueError("vacancy hh_id already exists")

        created = replace(
            vacancy,
            id=self._next_vacancy(),
            created_at=now(),
            updated_at=now(),
        )
        self.vacancies[id_of(created)] = created
        return created

    async def get_by_id(self, vacancy_id: int) -> Vacancy | None:
        return self.vacancies.get(vacancy_id)

    async def get_by_hh_id(self, hh_id: int) -> Vacancy | None:
        return next(
            (vacancy for vacancy in self.vacancies.values() if vacancy.hh_id == hh_id),
            None,
        )

    async def update_vacancy_cache(
        self,
        vacancy_id: int,
        title: str,
        url: str | None,
        raw_payload: dict[str, object] | None,
        cached_at: datetime | None,
        employer_id: int | None = None,
    ) -> Vacancy | None:
        vacancy = self.vacancies.get(vacancy_id)
        if vacancy is None:
            return None

        updated = replace(
            vacancy,
            title=title,
            url=url,
            raw_payload=raw_payload,
            cached_at=cached_at,
            employer_id=employer_id or vacancy.employer_id,
            updated_at=now(),
        )
        self.vacancies[vacancy_id] = updated
        return updated

    def _next_employer(self) -> int:
        value = self._next_employer_id
        self._next_employer_id += 1
        return value

    def _next_vacancy(self) -> int:
        value = self._next_vacancy_id
        self._next_vacancy_id += 1
        return value


class FakeSubscriptionRepo:
    def __init__(self) -> None:
        self._next_id = 1
        self.subscriptions: dict[int, Subscription] = {}

    async def create(self, subscription: Subscription) -> Subscription:
        created = replace(
            subscription,
            id=self._next(),
            created_at=now(),
            updated_at=now(),
        )
        self.subscriptions[id_of(created)] = created
        return created

    async def get_active_by_user_id(self, user_id: int) -> Subscription | None:
        active = [
            subscription
            for subscription in self.subscriptions.values()
            if subscription.user_id == user_id
            and subscription.status == SubscriptionStatus.ACTIVE
        ]
        if not active:
            return None

        return max(active, key=lambda subscription: subscription.expires_at)

    async def update_status(
        self,
        subscription_id: int,
        status: SubscriptionStatus,
    ) -> Subscription | None:
        subscription = self.subscriptions.get(subscription_id)
        if subscription is None:
            return None

        updated = replace(subscription, status=status, updated_at=now())
        self.subscriptions[subscription_id] = updated
        return updated

    async def list_active_expired_before(self, now: datetime) -> list[Subscription]:
        return [
            subscription
            for subscription in self.subscriptions.values()
            if subscription.status == SubscriptionStatus.ACTIVE
            and subscription.expires_at < now
        ]

    def _next(self) -> int:
        value = self._next_id
        self._next_id += 1
        return value


def now() -> datetime:
    return datetime.now(UTC)


def id_of(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise ValueError("entity id is not assigned")

    return entity_id
