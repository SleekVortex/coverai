from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.ports import (
    GenerationRequestRepo,
    ResumeProfileRepo,
    SubscriptionRepo,
    UserRepo,
    VacancyRepo,
)
from coverai.domain.user_registration_repo import UserRegistrationRepo
from coverai.repos.credit_ledger_sqlalchemy import CreditLedgerSqlAlchemyRepo
from coverai.repos.sqlalchemy import (
    GenerationRequestSqlAlchemyRepo,
    ResumeProfileSqlAlchemyRepo,
    SubscriptionSqlAlchemyRepo,
    UserSqlAlchemyRepo,
    VacancySqlAlchemyRepo,
)


class RepositoryProvider(Provider):
    @provide(scope=Scope.REQUEST, provides=UserRegistrationRepo)
    def user_registration_repo(self, session: AsyncSession) -> UserSqlAlchemyRepo:
        """Создает repo регистрации пользователей."""
        return UserSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=UserRepo)
    def user_repo(self, session: AsyncSession) -> UserSqlAlchemyRepo:
        """Создает repo пользователей."""
        return UserSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=CreditLedgerRepo)
    def credit_ledger_repo(self, session: AsyncSession) -> CreditLedgerSqlAlchemyRepo:
        """Создает repo кредитного ledger."""
        return CreditLedgerSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=ResumeProfileRepo)
    def resume_profile_repo(self, session: AsyncSession) -> ResumeProfileSqlAlchemyRepo:
        """Создает repo профилей резюме."""
        return ResumeProfileSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=GenerationRequestRepo)
    def generation_request_repo(
        self,
        session: AsyncSession,
    ) -> GenerationRequestSqlAlchemyRepo:
        """Создает repo запросов генерации."""
        return GenerationRequestSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=VacancyRepo)
    def vacancy_repo(self, session: AsyncSession) -> VacancySqlAlchemyRepo:
        """Создает repo вакансий."""
        return VacancySqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=SubscriptionRepo)
    def subscription_repo(self, session: AsyncSession) -> SubscriptionSqlAlchemyRepo:
        """Создает repo подписок."""
        return SubscriptionSqlAlchemyRepo(session)
