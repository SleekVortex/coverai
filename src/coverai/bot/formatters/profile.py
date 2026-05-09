from coverai.domain.entities import ResumeProfile
from coverai.services.profile import ProfileResult


def format_profile(profile: ResumeProfile) -> str:
    """Форматирует профиль резюме."""
    preview = profile.resume_text[:1200]
    suffix = (
        "\n\nℹ️ Показал первые 1200 символов. Полный текст сохранен."
        if len(profile.resume_text) > 1200
        else ""
    )
    return f"📄 Профиль\n\n{preview}{suffix}"


def format_profile_saved(result: ProfileResult) -> str:
    """Форматирует результат сохранения профиля."""
    if result.was_truncated:
        return (
            "✅ Профиль сохранен\n\n"
            "Текст был обрезан до 6000 символов.\n"
            "Теперь пришлите ссылку на вакансию hh.ru."
        )

    return "✅ Профиль сохранен\n\nТеперь пришлите ссылку на вакансию hh.ru."
