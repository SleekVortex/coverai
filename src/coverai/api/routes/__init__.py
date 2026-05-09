from fastapi import APIRouter

from coverai.api.routes.admin import router as admin_router
from coverai.api.routes.analytics import router as analytics_router
from coverai.api.routes.auth import router as auth_router
from coverai.api.routes.billing import router as billing_router
from coverai.api.routes.generations import router as generations_router
from coverai.api.routes.payments import router as payments_router
from coverai.api.routes.profile import router as profile_router
from coverai.api.routes.promocodes import router as promocodes_router
from coverai.api.routes.subscriptions import router as subscriptions_router
from coverai.api.routes.system import router as system_router
from coverai.api.routes.users import router as users_router

ROUTERS: tuple[APIRouter, ...] = (
    system_router,
    auth_router,
    users_router,
    profile_router,
    generations_router,
    billing_router,
    payments_router,
    subscriptions_router,
    promocodes_router,
    admin_router,
    analytics_router,
)

__all__ = ["ROUTERS"]
