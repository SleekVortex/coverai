from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from coverai.api.dependencies.auth import AdminUserDep, CurrentUserDep
from coverai.api.dependencies.session import SessionDep
from coverai.api.helpers.promo import (
    promo_by_code,
    promo_was_redeemed,
    validate_promo,
)
from coverai.api.helpers.users import locked_user
from coverai.api.schemas import PromoCreateRequest, PromoRedeemRequest, PromoResponse
from coverai.domain.enums import CreditTransactionType, PromoCodeType
from coverai.infra.db import models

router = APIRouter(tags=["promocodes"])


@router.post("/admin/promocodes", response_model=PromoResponse)
async def create_promo(
    payload: PromoCreateRequest,
    user: AdminUserDep,
    session: SessionDep,
) -> PromoResponse:
    """Создает промокод."""
    promo = models.PromoCode(
        code=payload.code.strip().upper(),
        type=payload.type.value,
        value=payload.value,
        valid_until=payload.valid_until,
        max_activations=payload.max_activations,
    )
    session.add(promo)
    try:
        await session.flush()
    except IntegrityError as error:
        raise HTTPException(status_code=409, detail="Promo code exists") from error
    return PromoResponse(
        code=promo.code,
        type=PromoCodeType(promo.type),
        value=promo.value,
        message=f"Promo code created by user {user.id}",
    )


@router.post("/promocodes/redeem", response_model=PromoResponse)
async def redeem_promo(
    payload: PromoRedeemRequest,
    user: CurrentUserDep,
    session: SessionDep,
) -> PromoResponse:
    """Активирует промокод."""
    promo = await promo_by_code(session, payload.code)
    if promo is None:
        raise HTTPException(status_code=404, detail="Promo code not found")
    if await promo_was_redeemed(session, promo.id, user.id):
        raise HTTPException(status_code=409, detail="Promo code already redeemed")
    validate_promo(promo)

    locked = await locked_user(session, user.id)
    promo.activations_count += 1
    session.add(models.PromoRedemption(promo_code_id=promo.id, user_id=user.id))
    if promo.type == PromoCodeType.FIXED_CREDITS.value:
        locked.credits += promo.value
        session.add(
            models.CreditTransaction(
                user_id=user.id,
                type=CreditTransactionType.PROMO.value,
                amount=promo.value,
                balance_after=locked.credits,
                description=f"Promo code {promo.code}",
                promo_code_id=promo.id,
            ),
        )
        message = f"Added {promo.value} credits"
    else:
        locked.pending_top_up_discount_percent = promo.value
        locked.pending_top_up_discount_valid_until = promo.valid_until
        locked.pending_top_up_discount_promo_code_id = promo.id
        message = f"Next top-up discount is {promo.value}%"

    await session.flush()
    return PromoResponse(
        code=promo.code,
        type=PromoCodeType(promo.type),
        value=promo.value,
        message=message,
    )
