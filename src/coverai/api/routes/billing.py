from fastapi import APIRouter, Request
from sqlalchemy import select

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.api.schemas import PlanUsageResponse, RecentCreditTransactionResponse
from coverai.infra.db import models
from coverai.repos.sqlalchemy import (
    GenerationRequestSqlAlchemyRepo,
    SubscriptionSqlAlchemyRepo,
    UserSqlAlchemyRepo,
)
from coverai.services.billing import QuotaService

router = APIRouter(tags=["billing"])


@router.get("/billing/balance", response_model=PlanUsageResponse)
async def balance(
    user: CurrentUserDep,
    session: SessionDep,
    request: Request,
) -> PlanUsageResponse:
    """Возвращает баланс пользователя."""
    usage = await QuotaService(
        user_repo=UserSqlAlchemyRepo(session),
        subscription_repo=SubscriptionSqlAlchemyRepo(session),
        generation_request_repo=GenerationRequestSqlAlchemyRepo(session),
    ).get_plan_usage(user.id)
    rows = await _recent_transactions(session, user.id)
    return PlanUsageResponse(
        plan=usage.plan.value,
        used=usage.used,
        limit=usage.limit,
        remaining=usage.remaining,
        period=usage.period,
        credits=user.credits,
        generation_cost_credits=request.app.state.settings.billing.prediction_cost_credits,
        recent_transactions=[_transaction_payload(row) for row in rows],
    )


@router.get("/billing/transactions")
async def transactions(
    user: CurrentUserDep,
    session: SessionDep,
) -> list[RecentCreditTransactionResponse]:
    """Возвращает операции по кредитам."""
    statement = (
        select(models.CreditTransaction)
        .where(models.CreditTransaction.user_id == user.id)
        .order_by(models.CreditTransaction.created_at.desc())
    )
    rows = await session.scalars(statement)
    return [_transaction_payload(row) for row in rows]


async def _recent_transactions(
    session: SessionDep,
    user_id: int,
    limit: int = 5,
) -> list[models.CreditTransaction]:
    statement = (
        select(models.CreditTransaction)
        .where(models.CreditTransaction.user_id == user_id)
        .order_by(models.CreditTransaction.created_at.desc())
        .limit(limit)
    )
    return list(await session.scalars(statement))


def _transaction_payload(
    row: models.CreditTransaction,
) -> RecentCreditTransactionResponse:
    return RecentCreditTransactionResponse(
        id=row.id,
        type=row.type,
        amount=row.amount,
        balance_after=row.balance_after,
        description=row.description,
        created_at=row.created_at,
    )
