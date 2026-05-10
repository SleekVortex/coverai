from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.ports import (
    AdminReadRepo,
    AnalyticsReadRepo,
    BillingReadRepo,
    CoverLetterRepo,
    GenerationRequestRepo,
    PaymentRepo,
    PromoCodeRepo,
    ResumeProfileRepo,
    SubscriptionPaymentRepo,
    SubscriptionRepo,
    UserRepo,
    VacancyRepo,
)
from coverai.domain.user_registration_repo import UserRegistrationRepo
from coverai.repos.credit_ledger_sqlalchemy import CreditLedgerSqlAlchemyRepo
from coverai.repos.sqlalchemy import (
    AdminReadSqlAlchemyRepo,
    AnalyticsReadSqlAlchemyRepo,
    BillingReadSqlAlchemyRepo,
    CoverLetterSqlAlchemyRepo,
    GenerationRequestSqlAlchemyRepo,
    PaymentSqlAlchemyRepo,
    PromoCodeSqlAlchemyRepo,
    ResumeProfileSqlAlchemyRepo,
    SubscriptionPaymentSqlAlchemyRepo,
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

    @provide(scope=Scope.REQUEST, provides=CoverLetterRepo)
    def cover_letter_repo(self, session: AsyncSession) -> CoverLetterSqlAlchemyRepo:
        """Создает repo сопроводительных писем."""
        return CoverLetterSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=PaymentRepo)
    def payment_repo(self, session: AsyncSession) -> PaymentSqlAlchemyRepo:
        """Создает repo платежей."""
        return PaymentSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=PromoCodeRepo)
    def promo_code_repo(self, session: AsyncSession) -> PromoCodeSqlAlchemyRepo:
        """Создает repo промокодов."""
        return PromoCodeSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=SubscriptionPaymentRepo)
    def subscription_payment_repo(
        self,
        session: AsyncSession,
    ) -> SubscriptionPaymentSqlAlchemyRepo:
        """Создает repo платежей подписки."""
        return SubscriptionPaymentSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=BillingReadRepo)
    def billing_read_repo(self, session: AsyncSession) -> BillingReadSqlAlchemyRepo:
        """Создает read repo биллинга."""
        return BillingReadSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=AnalyticsReadRepo)
    def analytics_read_repo(
        self,
        session: AsyncSession,
    ) -> AnalyticsReadSqlAlchemyRepo:
        """Создает read repo аналитики."""
        return AnalyticsReadSqlAlchemyRepo(session)

    @provide(scope=Scope.REQUEST, provides=AdminReadRepo)
    def admin_read_repo(self, session: AsyncSession) -> AdminReadSqlAlchemyRepo:
        """Создает read repo админки."""
        return AdminReadSqlAlchemyRepo(session)
