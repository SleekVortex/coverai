from dishka import Provider, Scope, provide

from coverai.configs import Settings
from coverai.domain.credit_ledger_repo import CreditLedgerRepo
from coverai.domain.generation_job_queue import GenerationJobQueue
from coverai.domain.ports import (
    GenerationRequestRepo,
    ResumeProfileRepo,
    SubscriptionRepo,
    UserRepo,
    VacancyRepo,
)
from coverai.domain.user_registration_repo import UserRegistrationRepo
from coverai.services.billing import QuotaService
from coverai.services.credits import CreditLedgerService
from coverai.services.generation import GenerationQueueService
from coverai.services.users import UserRegistrationService


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
