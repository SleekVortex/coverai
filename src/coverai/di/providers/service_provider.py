from dishka import Provider, Scope, provide

from coverai.configs import Settings
from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.generation_job_queue import GenerationJobQueue
from coverai.domain.ports import (
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
from coverai.services.billing import (
    AdminCommandService,
    PaymentService,
    PromoService,
    QuotaService,
    SubscriptionPaymentService,
)
from coverai.services.credits import CreditLedgerService
from coverai.services.generation import GenerationQueueService
from coverai.services.history import HistoryService
from coverai.services.profile import ProfileService
from coverai.services.users import UserRegistrationService, UserService


class ServiceProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def credit_ledger_service(
        self,
        credit_ledger_repo: CreditLedgerRepo,
    ) -> CreditLedgerService:
        """Создает сервис кредитного ledger."""
        return CreditLedgerService(credit_ledger_repo)

    @provide(scope=Scope.REQUEST)
    def user_registration_service(
        self,
        user_repo: UserRegistrationRepo,
        credit_ledger_service: CreditLedgerService,
        settings: Settings,
    ) -> UserRegistrationService:
        """Создает сервис регистрации пользователей."""
        return UserRegistrationService(
            user_repo=user_repo,
            credit_ledger_service=credit_ledger_service,
            welcome_credits=settings.billing.prediction_cost_credits,
        )

    @provide(scope=Scope.REQUEST)
    def quota_service(
        self,
        user_repo: UserRepo,
        subscription_repo: SubscriptionRepo,
        generation_request_repo: GenerationRequestRepo,
    ) -> QuotaService:
        """Создает сервис квот."""
        return QuotaService(
            user_repo=user_repo,
            subscription_repo=subscription_repo,
            generation_request_repo=generation_request_repo,
        )

    @provide(scope=Scope.REQUEST)
    def user_service(self, user_repo: UserRepo) -> UserService:
        """Создает сервис пользователей."""
        return UserService(user_repo)

    @provide(scope=Scope.REQUEST)
    def profile_service(self, profile_repo: ResumeProfileRepo) -> ProfileService:
        """Создает сервис профилей."""
        return ProfileService(profile_repo)

    @provide(scope=Scope.REQUEST)
    def history_service(
        self,
        user_repo: UserRepo,
        cover_letter_repo: CoverLetterRepo,
    ) -> HistoryService:
        """Создает сервис истории."""
        return HistoryService(
            user_repo=user_repo,
            cover_letter_repo=cover_letter_repo,
        )

    @provide(scope=Scope.REQUEST)
    def payment_service(
        self,
        payment_repo: PaymentRepo,
        user_repo: UserRepo,
        credit_ledger_repo: CreditLedgerRepo,
        settings: Settings,
    ) -> PaymentService:
        """Создает сервис платежей."""
        return PaymentService(
            payment_repo=payment_repo,
            user_repo=user_repo,
            credit_ledger_repo=credit_ledger_repo,
            credit_price_rub=settings.billing.credit_price_rub,
        )

    @provide(scope=Scope.REQUEST)
    def promo_service(
        self,
        promo_repo: PromoCodeRepo,
        user_repo: UserRepo,
        credit_ledger_repo: CreditLedgerRepo,
    ) -> PromoService:
        """Создает сервис промокодов."""
        return PromoService(
            promo_repo=promo_repo,
            user_repo=user_repo,
            credit_ledger_repo=credit_ledger_repo,
        )

    @provide(scope=Scope.REQUEST)
    def admin_command_service(
        self,
        user_repo: UserRepo,
        subscription_repo: SubscriptionRepo,
        credit_ledger_repo: CreditLedgerRepo,
    ) -> AdminCommandService:
        """Создает command-сервис админки."""
        return AdminCommandService(
            user_repo=user_repo,
            subscription_repo=subscription_repo,
            credit_ledger_repo=credit_ledger_repo,
        )

    @provide(scope=Scope.REQUEST)
    def subscription_payment_service(
        self,
        subscription_repo: SubscriptionRepo,
        subscription_payment_repo: SubscriptionPaymentRepo,
        settings: Settings,
    ) -> SubscriptionPaymentService:
        """Создает сервис платежей подписок."""
        return SubscriptionPaymentService(
            subscription_repo=subscription_repo,
            subscription_payment_repo=subscription_payment_repo,
            standard_price_rub=settings.billing.standard_subscription_price_rub,
            pro_price_rub=settings.billing.pro_subscription_price_rub,
        )

    @provide(scope=Scope.REQUEST)
    def generation_queue_service(
        self,
        user_repo: UserRepo,
        profile_repo: ResumeProfileRepo,
        generation_request_repo: GenerationRequestRepo,
        vacancy_repo: VacancyRepo,
        quota_service: QuotaService,
        generation_job_queue: GenerationJobQueue,
        settings: Settings,
    ) -> GenerationQueueService:
        """Создает сервис очереди генераций."""
        return GenerationQueueService(
            user_repo=user_repo,
            profile_repo=profile_repo,
            generation_request_repo=generation_request_repo,
            vacancy_repo=vacancy_repo,
            quota_service=quota_service,
            queue=generation_job_queue,
            cost_credits=settings.billing.prediction_cost_credits,
        )
