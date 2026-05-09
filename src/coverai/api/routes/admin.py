from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from coverai.api.dependencies.auth import AdminUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.domain.enums import CreditTransactionType, GenerationStatus, Plan
from coverai.infra.db import models

router = APIRouter(tags=["admin"])


class BalanceAdjustmentRequest(BaseModel):
    amount: int
    reason: str = Field(min_length=1)


@router.get("/admin/users")
async def list_users(
    user: AdminUserDep,
    session: SessionDep,
    limit: int = 20,
    offset: int = 0,
    plan: Plan | None = None,
    role: str | None = None,
) -> list[dict[str, Any]]:
    """Возвращает список пользователей."""
    statement = select(models.User)
    if plan is not None:
        statement = statement.where(models.User.plan == plan.value)
    if role is not None:
        statement = statement.where(models.User.role == role)
    rows = await session.scalars(statement.offset(offset).limit(limit))
    return [_user_summary(row) for row in rows]


@router.get("/admin/users/{id}")
async def user_detail(
    id: int,
    user: AdminUserDep,
    session: SessionDep,
) -> dict[str, Any]:
    """Возвращает детали пользователя."""
    target = await session.get(models.User, id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    profile = await session.scalar(
        select(models.ResumeProfile).where(models.ResumeProfile.user_id == id),
    )
    active_subscription = await _active_subscription(session, id)
    generation_counts = await _generation_counts(session, id)
    return {
        **_user_summary(target),
        "profile": None
        if profile is None
        else {
            "id": profile.id,
            "title": profile.title,
            "resume_text": profile.resume_text,
        },
        "balance_credits": target.credits,
        "active_subscription": _subscription_payload(active_subscription),
        "generation_counts": generation_counts,
    }


@router.post("/admin/users/{id}/balance-adjustment")
async def adjust_balance(
    id: int,
    payload: BalanceAdjustmentRequest,
    user: AdminUserDep,
    session: SessionDep,
) -> dict[str, Any]:
    """Изменяет баланс пользователя."""
    target = await session.scalar(
        select(models.User).where(models.User.id == id).with_for_update(),
    )
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    target.credits += payload.amount
    if target.credits < 0:
        raise HTTPException(status_code=409, detail="Balance cannot be negative")
    session.add(
        models.CreditTransaction(
            user_id=target.id,
            type=CreditTransactionType.ADJUSTMENT.value,
            amount=payload.amount,
            balance_after=target.credits,
            description=payload.reason,
            metadata_json={"reason": payload.reason, "admin_id": user.id},
        ),
    )
    await session.flush()
    return {"user_id": target.id, "balance_credits": target.credits}


@router.post("/admin/users/{id}/subscription/expire")
async def expire_subscription(
    id: int,
    user: AdminUserDep,
    session: SessionDep,
) -> dict[str, Any]:
    """Завершает подписку пользователя."""
    target = await session.get(models.User, id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    subscription = await _active_subscription(session, id)
    if subscription is not None:
        subscription.status = "expired"
    target.plan = Plan.FREE.value
    await session.flush()
    return {"user_id": id, "plan": target.plan, "subscription_status": "expired"}


@router.get("/admin/analytics/overview")
async def analytics_overview(
    user: AdminUserDep,
    session: SessionDep,
) -> dict[str, Any]:
    """Возвращает административную аналитику."""
    users_by_plan = {
        plan.value: int(
            await session.scalar(
                select(func.count())
                .select_from(models.User)
                .where(models.User.plan == plan.value),
            )
            or 0,
        )
        for plan in Plan
    }
    total_generations = int(
        await session.scalar(select(func.count()).select_from(models.GenerationRequest))
        or 0,
    )
    succeeded_generations = int(
        await session.scalar(
            select(func.count())
            .select_from(models.GenerationRequest)
            .where(models.GenerationRequest.status == GenerationStatus.SUCCEEDED.value),
        )
        or 0,
    )
    revenue = int(
        await session.scalar(
            select(func.coalesce(func.sum(models.PaymentIntent.amount_rub), 0)).where(
                models.PaymentIntent.status == "succeeded",
            ),
        )
        or 0,
    )
    active_subscriptions = int(
        await session.scalar(
            select(func.count())
            .select_from(models.Subscription)
            .where(models.Subscription.status == "active"),
        )
        or 0,
    )
    return {
        "users_by_plan": users_by_plan,
        "generations_per_day": total_generations,
        "success_rate": 0
        if total_generations == 0
        else succeeded_generations / total_generations,
        "revenue": revenue,
        "active_subscriptions": active_subscriptions,
    }


def _user_summary(row: models.User) -> dict[str, Any]:
    return {
        "id": row.id,
        "email": row.email,
        "telegram_id": row.telegram_id,
        "role": row.role,
        "plan": row.plan,
        "credits": row.credits,
    }


async def _active_subscription(
    session: SessionDep,
    user_id: int,
) -> models.Subscription | None:
    return await session.scalar(
        select(models.Subscription)
        .where(
            models.Subscription.user_id == user_id,
            models.Subscription.status == "active",
        )
        .order_by(models.Subscription.expires_at.desc()),
    )


async def _generation_counts(
    session: SessionDep,
    user_id: int,
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for status in GenerationStatus:
        counts[status.value] = int(
            await session.scalar(
                select(func.count())
                .select_from(models.GenerationRequest)
                .where(
                    models.GenerationRequest.user_id == user_id,
                    models.GenerationRequest.status == status.value,
                ),
            )
            or 0,
        )
    return counts


def _subscription_payload(row: models.Subscription | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {
        "id": row.id,
        "plan": row.plan,
        "starts_at": row.starts_at,
        "expires_at": row.expires_at,
    }
