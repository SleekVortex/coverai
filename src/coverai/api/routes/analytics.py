from fastapi import APIRouter
from sqlalchemy import func, select

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.api.schemas import AnalyticsResponse
from coverai.domain.enums import CreditTransactionType, GenerationStatus
from coverai.infra.db import models

router = APIRouter(tags=["analytics"])


@router.get("/analytics/usage", response_model=AnalyticsResponse)
async def analytics(user: CurrentUserDep, session: SessionDep) -> AnalyticsResponse:
    """Возвращает пользовательскую аналитику."""
    total = await session.scalar(
        select(func.count())
        .select_from(models.GenerationRequest)
        .where(models.GenerationRequest.user_id == user.id),
    )
    succeeded = await session.scalar(
        select(func.count())
        .select_from(models.GenerationRequest)
        .where(
            models.GenerationRequest.user_id == user.id,
            models.GenerationRequest.status == GenerationStatus.SUCCEEDED.value,
        ),
    )
    failed = await session.scalar(
        select(func.count())
        .select_from(models.GenerationRequest)
        .where(
            models.GenerationRequest.user_id == user.id,
            models.GenerationRequest.status == GenerationStatus.FAILED.value,
        ),
    )
    spent = await session.scalar(
        select(func.coalesce(func.sum(models.CreditTransaction.amount), 0)).where(
            models.CreditTransaction.user_id == user.id,
            models.CreditTransaction.type == CreditTransactionType.SPEND.value,
        ),
    )
    return AnalyticsResponse(
        total_generations=int(total or 0),
        succeeded_generations=int(succeeded or 0),
        failed_generations=int(failed or 0),
        credits_spent=abs(int(spent or 0)),
    )
