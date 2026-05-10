from dataclasses import asdict
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from coverai.api.dependencies.auth import AdminUserDep
from coverai.api.dependencies.services import AdminCommandServiceDep, AdminReadRepoDep
from coverai.domain.enums import Plan
from coverai.domain.ids import required_id
from coverai.services.billing.errors import UserBalanceCannotBeNegativeError
from coverai.services.users.errors import UserNotFoundError

router = APIRouter(tags=["admin"])


class BalanceAdjustmentRequest(BaseModel):
    amount: int
    reason: str = Field(min_length=1)


@router.get("/admin/users")
async def list_users(
    user: AdminUserDep,
    admin_read_repo: AdminReadRepoDep,
    limit: int = 20,
    offset: int = 0,
    plan: Plan | None = None,
    role: str | None = None,
) -> list[dict[str, Any]]:
    """Возвращает список пользователей."""
    rows = await admin_read_repo.list_users(
        limit=limit,
        offset=offset,
        plan=plan,
        role=role,
    )
    return [asdict(row) for row in rows]


@router.get("/admin/users/{id}")
async def user_detail(
    id: int,
    user: AdminUserDep,
    admin_read_repo: AdminReadRepoDep,
) -> dict[str, Any]:
    """Возвращает детали пользователя."""
    detail = await admin_read_repo.user_detail(id)
    if detail is None:
        raise HTTPException(status_code=404, detail="User not found")

    payload = asdict(detail.summary)
    payload.update(
        {
            "profile": None if detail.profile is None else asdict(detail.profile),
            "balance_credits": detail.balance_credits,
            "active_subscription": None
            if detail.active_subscription is None
            else asdict(detail.active_subscription),
            "generation_counts": detail.generation_counts,
        },
    )
    return payload


@router.post("/admin/users/{id}/balance-adjustment")
async def adjust_balance(
    id: int,
    payload: BalanceAdjustmentRequest,
    user: AdminUserDep,
    admin_command_service: AdminCommandServiceDep,
) -> dict[str, Any]:
    """Изменяет баланс пользователя."""
    try:
        return await admin_command_service.adjust_balance(
            user_id=id,
            amount=payload.amount,
            reason=payload.reason,
            admin_id=required_id(user),
        )
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="User not found") from error
    except UserBalanceCannotBeNegativeError as error:
        raise HTTPException(
            status_code=409,
            detail="Balance cannot be negative",
        ) from error


@router.post("/admin/users/{id}/subscription/expire")
async def expire_subscription(
    id: int,
    user: AdminUserDep,
    admin_command_service: AdminCommandServiceDep,
) -> dict[str, Any]:
    """Завершает подписку пользователя."""
    try:
        return await admin_command_service.expire_subscription(id)
    except UserNotFoundError as error:
        raise HTTPException(status_code=404, detail="User not found") from error


@router.get("/admin/analytics/overview")
async def analytics_overview(
    user: AdminUserDep,
    admin_read_repo: AdminReadRepoDep,
) -> dict[str, Any]:
    """Возвращает административную аналитику."""
    return asdict(await admin_read_repo.analytics_overview())
