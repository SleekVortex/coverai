from coverai.domain.enums import Plan
from coverai.services.billing import PlanUsage


def format_plan_usage(usage: PlanUsage) -> str:
    """Форматирует использование тарифа."""
    return format_legacy_plan_usage(usage)


def format_legacy_plan_usage(usage: PlanUsage) -> str:
    """Форматирует legacy-текст тарифа."""
    if usage.is_unlimited:
        return (
            f"📊 Мой лимит\n\nТариф: {plan_label(usage.plan)}\nЛимит: ♾️ без ограничений"
        )

    remaining = usage.remaining if usage.remaining is not None else 0
    return (
        "📊 Мой лимит\n\n"
        f"Тариф: {plan_label(usage.plan)}\n"
        f"Период: {period_label(usage.period)}\n"
        f"Использовано: {usage.used} из {usage.limit}\n"
        f"Осталось писем: {remaining}"
    )


def plan_label(plan: Plan) -> str:
    """Возвращает название тарифа."""
    if plan == Plan.FREE:
        return "Free"
    if plan == Plan.STANDARD:
        return "Standard"

    return "Pro"


def period_label(period: str | None) -> str:
    """Возвращает название периода."""
    if period == "day":
        return "сегодня"
    if period == "month":
        return "в этом месяце"

    return "текущий период"
