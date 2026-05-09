from coverai.domain.enums import Plan
from coverai.services.billing.models import PlanLimits
from coverai.services.config import SERVICE_CONFIG


def plan_limits(plan: Plan) -> PlanLimits:
    """Возвращает лимиты тарифа."""
    limits = SERVICE_CONFIG.billing.plan_limits[plan]
    return PlanLimits(plan=plan, limit=limits.limit, period=limits.period)
