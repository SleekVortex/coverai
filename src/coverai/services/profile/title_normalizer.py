from coverai.services.config import SERVICE_CONFIG
from coverai.services.profile.errors import InvalidProfileTitleError

MAX_PROFILE_TITLE_LENGTH = SERVICE_CONFIG.profile.max_profile_title_length


def normalize_profile_title(title: str) -> str:
    """Нормализует название профиля."""
    normalized = title.strip()
    if not normalized or len(normalized) > MAX_PROFILE_TITLE_LENGTH:
        raise InvalidProfileTitleError

    return normalized
