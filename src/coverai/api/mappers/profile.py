from coverai.api.schemas import ProfileResponse
from coverai.services.profile import ProfileResult


def profile_response(result: ProfileResult) -> ProfileResponse:
    """Преобразует профиль в API response."""
    return ProfileResponse(
        id=result.profile.id or 0,
        title=result.profile.title,
        resume_text=result.profile.resume_text,
        was_truncated=result.was_truncated,
    )
