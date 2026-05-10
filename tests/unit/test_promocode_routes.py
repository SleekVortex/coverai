import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from coverai.api.dependencies.auth import current_user
from coverai.api.dependencies.services import get_promo_service
from coverai.api.routes.promocodes import router
from coverai.domain.entities import User
from coverai.services.billing.errors import (
    PromoCodeActivationLimitReachedError,
    PromoCodeExpiredError,
    PromoCodeInactiveError,
    PromoCodeInvalidError,
)


@pytest.mark.parametrize(
    ("error_type", "detail"),
    [
        (PromoCodeInactiveError, "Promo code is inactive"),
        (PromoCodeExpiredError, "Promo code expired"),
        (
            PromoCodeActivationLimitReachedError,
            "Promo code activation limit reached",
        ),
    ],
)
def test_redeem_promo_maps_invalid_reason_to_http_400(
    error_type: type[PromoCodeInvalidError],
    detail: str,
) -> None:
    app = FastAPI()
    app.include_router(router)
    service = RaisingPromoService(error_type())

    async def override_current_user() -> User:
        return User(id=1, telegram_id=None)

    async def override_promo_service() -> RaisingPromoService:
        return service

    app.dependency_overrides[current_user] = override_current_user
    app.dependency_overrides[get_promo_service] = override_promo_service

    with TestClient(app) as client:
        response = client.post("/promocodes/redeem", json={"code": "test"})

    assert response.status_code == 400
    assert response.json()["detail"] == detail


class RaisingPromoService:
    def __init__(self, error: PromoCodeInvalidError) -> None:
        self._error = error

    async def redeem(self, _user: User, _code: str) -> object:
        raise self._error
