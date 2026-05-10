from fastapi import APIRouter

from coverai.api.dependencies.auth import CurrentUserDep
from coverai.api.dependencies.services import AnalyticsReadRepoDep
from coverai.api.schemas import AnalyticsResponse
from coverai.domain.ids import required_id

router = APIRouter(tags=["analytics"])


@router.get("/analytics/usage", response_model=AnalyticsResponse)
async def analytics(
    user: CurrentUserDep,
    analytics_read_repo: AnalyticsReadRepoDep,
) -> AnalyticsResponse:
    """Возвращает пользовательскую аналитику."""
    usage = await analytics_read_repo.user_usage(required_id(user))
    return AnalyticsResponse(
        total_generations=usage.total_generations,
        succeeded_generations=usage.succeeded_generations,
        failed_generations=usage.failed_generations,
        credits_spent=usage.credits_spent,
    )
