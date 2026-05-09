from typing import Any

from coverai.domain.enums import Plan

_PLAN_PRIORITY = {
    Plan.PRO: 0,
    Plan.STANDARD: 1,
    Plan.FREE: 2,
}


def select_next_generation_task(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Выбирает следующую задачу генерации."""
    if not tasks:
        raise ValueError("task queue is empty")
    return min(tasks, key=lambda task: _PLAN_PRIORITY[Plan(task["plan"])])
