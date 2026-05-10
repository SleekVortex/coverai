from fastapi import APIRouter, HTTPException

from coverai.api.dependencies.auth import AdminUserDep, CurrentUserDep
from coverai.api.dependencies.services import PromoServiceDep
from coverai.api.schemas import PromoCreateRequest, PromoRedeemRequest, PromoResponse
from coverai.domain.enums import PromoCodeType
from coverai.domain.ids import required_id
from coverai.services.billing.errors import (
    PromoCodeActivationLimitReachedError,
    PromoCodeAlreadyExistsError,
    PromoCodeAlreadyRedeemedError,
    PromoCodeExpiredError,
    PromoCodeInactiveError,
    PromoCodeInvalidError,
    PromoCodeNotFoundError,
)

router = APIRouter(tags=["promocodes"])


@router.post("/admin/promocodes", response_model=PromoResponse)
async def create_promo(
    payload: PromoCreateRequest,
    user: AdminUserDep,
    promo_service: PromoServiceDep,
) -> PromoResponse:
    """Создает промокод."""
    try:
        promo = await promo_service.create_promo(
            code=payload.code,
            type=payload.type,
            value=payload.value,
            valid_until=payload.valid_until,
            max_activations=payload.max_activations,
        )
    except PromoCodeAlreadyExistsError as error:
        raise HTTPException(status_code=409, detail="Promo code exists") from error
    return PromoResponse(
        code=promo.code,
        type=PromoCodeType(promo.type),
        value=promo.value,
        message=f"Promo code created by user {required_id(user)}",
    )


@router.post("/promocodes/redeem", response_model=PromoResponse)
async def redeem_promo(
    payload: PromoRedeemRequest,
    user: CurrentUserDep,
    promo_service: PromoServiceDep,
) -> PromoResponse:
    """Активирует промокод."""
    try:
        result = await promo_service.redeem(user, payload.code)
    except PromoCodeNotFoundError as error:
        raise HTTPException(status_code=404, detail="Promo code not found") from error
    except PromoCodeAlreadyRedeemedError as error:
        raise HTTPException(
            status_code=409,
            detail="Promo code already redeemed",
        ) from error
    except PromoCodeInactiveError as error:
        raise HTTPException(status_code=400, detail="Promo code is inactive") from error
    except PromoCodeExpiredError as error:
        raise HTTPException(status_code=400, detail="Promo code expired") from error
    except PromoCodeActivationLimitReachedError as error:
        raise HTTPException(
            status_code=400,
            detail="Promo code activation limit reached",
        ) from error
    except PromoCodeInvalidError as error:
        raise HTTPException(status_code=400, detail="Promo code is invalid") from error

    return PromoResponse(
        code=result.promo.code,
        type=PromoCodeType(result.promo.type),
        value=result.promo.value,
        message=result.message,
    )
