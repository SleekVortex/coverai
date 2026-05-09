from coverai.services.config import SERVICE_CONFIG
from coverai.services.profile.errors import ResumeTextTooShortError
from coverai.services.profile.models import NormalizedResumeText

MIN_RESUME_TEXT_LENGTH = SERVICE_CONFIG.profile.min_resume_text_length
MAX_RESUME_TEXT_LENGTH = SERVICE_CONFIG.profile.max_resume_text_length


def normalize_resume_text(resume_text: str) -> NormalizedResumeText:
    """Нормализует текст резюме."""
    normalized = resume_text.strip()
    if len(normalized) < MIN_RESUME_TEXT_LENGTH:
        raise ResumeTextTooShortError

    if len(normalized) > MAX_RESUME_TEXT_LENGTH:
        return NormalizedResumeText(
            text=normalized[:MAX_RESUME_TEXT_LENGTH],
            was_truncated=True,
        )

    return NormalizedResumeText(text=normalized, was_truncated=False)
