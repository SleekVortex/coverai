from collections.abc import AsyncIterator
from typing import Annotated

from dishka import Scope
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from coverai.api.dependencies.session import SessionDep
from coverai.domain.generation_job_queue import GenerationJobQueue
from coverai.infra.arq_generation_job_queue import ArqGenerationJobQueue
from coverai.services.generation import GenerationQueueService
from coverai.services.users import UserRegistrationService


async def get_user_registration_service(
    request: Request,
    session: SessionDep,
) -> AsyncIterator[UserRegistrationService]:
    """Возвращает значение."""
    container = request.app.state.dishka_container
    async with container({AsyncSession: session}, scope=Scope.REQUEST) as request_scope:
        yield await request_scope.get(UserRegistrationService)


RegistrationServiceDep = Annotated[
    UserRegistrationService,
    Depends(get_user_registration_service),
]


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
