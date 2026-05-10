from fastapi import APIRouter, Request

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.services import BillingReadRepoDep, QuotaServiceDep
from coverai.api.schemas import PlanUsageResponse, RecentCreditTransactionResponse
from coverai.domain.ids import required_id
from coverai.domain.read_models import CreditTransactionRead

router = APIRouter(tags=["billing"])


@router.get("/billing/balance", response_model=PlanUsageResponse)
async def balance(
    user: CurrentUserDep,
    quota_service: QuotaServiceDep,
    billing_read_repo: BillingReadRepoDep,
    request: Request,
) -> PlanUsageResponse:
    """Возвращает баланс пользователя."""
    user_id = required_id(user)
    usage = await quota_service.get_plan_usage_for_user(user)
    summary = await billing_read_repo.billing_summary(user_id)
    return PlanUsageResponse(
        plan=usage.plan.value,
        used=usage.used,
        limit=usage.limit,
        remaining=usage.remaining,
        period=usage.period,
        credits=summary.credits,
        generation_cost_credits=request.app.state.settings.billing.prediction_cost_credits,
        recent_transactions=[
            _transaction_payload(row) for row in summary.recent_transactions
        ],
    )


@router.get("/billing/transactions")
async def transactions(
    user: CurrentUserDep,
    billing_read_repo: BillingReadRepoDep,
) -> list[RecentCreditTransactionResponse]:
    """Возвращает операции по кредитам."""
    rows = await billing_read_repo.transactions(required_id(user))
    return [_transaction_payload(row) for row in rows]


def _transaction_payload(
    row: CreditTransactionRead,
) -> RecentCreditTransactionResponse:
    return RecentCreditTransactionResponse(
        id=row.id,
        type=row.type,
        amount=row.amount,
        balance_after=row.balance_after,
        description=row.description,
        created_at=row.created_at,
    )
