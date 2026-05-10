from collections.abc import AsyncIterator
from typing import Annotated, cast

from dishka import Scope
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.api.dependencies.session import SessionDep
from coverai.domain.generation_job_queue import GenerationJobQueue
from coverai.domain.ports import AdminReadRepo, AnalyticsReadRepo, BillingReadRepo
from coverai.infra.arq_generation_job_queue import ArqGenerationJobQueue
from coverai.services.billing import (
    AdminCommandService,
    PaymentService,
    PromoService,
    QuotaService,
    SubscriptionPaymentService,
)
from coverai.services.generation import GenerationQueueService
from coverai.services.history import HistoryService
from coverai.services.profile import ProfileService
from coverai.services.users import UserRegistrationService, UserService


async def _request_scoped_dependency[T](
    request: Request,
    session: AsyncSession,
    dependency_type: type[T],
) -> AsyncIterator[T]:
    container = request.app.state.dishka_container
    async with container({AsyncSession: session}, scope=Scope.REQUEST) as request_scope:
        yield await request_scope.get(dependency_type)


async def get_user_registration_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[UserRegistrationService]:
    """Возвращает значение."""
    async for service in _request_scoped_dependency(
        request,
        session,
        UserRegistrationService,
    ):
        yield service


RegistrationServiceDep = Annotated[
    UserRegistrationService,
    Depends(get_user_registration_service),
]


async def get_user_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[UserService]:
    """Возвращает сервис пользователей."""
    async for service in _request_scoped_dependency(request, session, UserService):
        yield service


UserServiceDep = Annotated[UserService, Depends(get_user_service)]


async def get_profile_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[ProfileService]:
    """Возвращает сервис профилей."""
    async for service in _request_scoped_dependency(request, session, ProfileService):
        yield service


ProfileServiceDep = Annotated[ProfileService, Depends(get_profile_service)]


async def get_history_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[HistoryService]:
    """Возвращает сервис истории."""
    async for service in _request_scoped_dependency(request, session, HistoryService):
        yield service


HistoryServiceDep = Annotated[HistoryService, Depends(get_history_service)]


async def get_quota_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[QuotaService]:
    """Возвращает сервис квот."""
    async for service in _request_scoped_dependency(request, session, QuotaService):
        yield service


QuotaServiceDep = Annotated[QuotaService, Depends(get_quota_service)]


async def get_payment_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[PaymentService]:
    """Возвращает сервис платежей."""
    async for service in _request_scoped_dependency(request, session, PaymentService):
        yield service


PaymentServiceDep = Annotated[PaymentService, Depends(get_payment_service)]


async def get_promo_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[PromoService]:
    """Возвращает сервис промокодов."""
    async for service in _request_scoped_dependency(request, session, PromoService):
        yield service


PromoServiceDep = Annotated[PromoService, Depends(get_promo_service)]


async def get_admin_command_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[AdminCommandService]:
    """Возвращает command-сервис админки."""
    async for service in _request_scoped_dependency(
        request,
        session,
        AdminCommandService,
    ):
        yield service


AdminCommandServiceDep = Annotated[
    AdminCommandService,
    Depends(get_admin_command_service),
]


async def get_subscription_payment_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[SubscriptionPaymentService]:
    """Возвращает сервис платежей подписок."""
    async for service in _request_scoped_dependency(
        request,
        session,
        SubscriptionPaymentService,
    ):
        yield service


SubscriptionPaymentServiceDep = Annotated[
    SubscriptionPaymentService,
    Depends(get_subscription_payment_service),
]


async def get_billing_read_repo(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[BillingReadRepo]:
    """Возвращает read repo биллинга."""
    dependency_type = cast(type[BillingReadRepo], BillingReadRepo)
    async for repo in _request_scoped_dependency(request, session, dependency_type):
        yield repo


BillingReadRepoDep = Annotated[BillingReadRepo, Depends(get_billing_read_repo)]


async def get_analytics_read_repo(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[AnalyticsReadRepo]:
    """Возвращает read repo аналитики."""
    dependency_type = cast(type[AnalyticsReadRepo], AnalyticsReadRepo)
    async for repo in _request_scoped_dependency(request, session, dependency_type):
        yield repo


AnalyticsReadRepoDep = Annotated[AnalyticsReadRepo, Depends(get_analytics_read_repo)]


async def get_admin_read_repo(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[AdminReadRepo]:
    """Возвращает read repo админки."""
    dependency_type = cast(type[AdminReadRepo], AdminReadRepo)
    async for repo in _request_scoped_dependency(request, session, dependency_type):
        yield repo


AdminReadRepoDep = Annotated[AdminReadRepo, Depends(get_admin_read_repo)]


async def get_generation_queue_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[GenerationQueueService]:
    """Возвращает значение."""
    queue: GenerationJobQueue = ArqGenerationJobQueue(request.app.state.arq_pool)
    container = request.app.state.dishka_container
    async with container(
        {AsyncSession: session, GenerationJobQueue: queue},
        scope=Scope.REQUEST,
    ) as request_scope:
        yield await request_scope.get(GenerationQueueService)


GenerationQueueServiceDep = Annotated[
    GenerationQueueService,
    Depends(get_generation_queue_service),
]
