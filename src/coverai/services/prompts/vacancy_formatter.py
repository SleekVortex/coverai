from coverai.domain.entities import Vacancy
from coverai.services.config import SERVICE_CONFIG
from coverai.services.prompts.text_normalizer import (
    html_to_text,
    normalize_text,
    truncate_text,
)

MAX_DESCRIPTION_LENGTH = SERVICE_CONFIG.prompts.vacancy_description_max_length


def vacancy_detail_lines(vacancy: Vacancy) -> list[str]:
    """Форматирует детали вакансии."""
    if vacancy.raw_payload is None:
        return []

    payload = vacancy.raw_payload
    lines: list[str] = []
    description = optional_text(payload, "description")
    if description is not None:
        description_text = normalize_text(html_to_text(description))
        lines.append(
            "Description: "
            + truncate_text(description_text, MAX_DESCRIPTION_LENGTH),
        )

    skills = named_items(payload.get("key_skills"))
    if skills:
        lines.append(f"Key skills: {', '.join(skills)}")

    return lines


def optional_text(payload: dict[str, object], field: str) -> str | None:
    """Возвращает необязательный текст."""
    value = payload.get(field)
    return value if isinstance(value, str) and value else None


def named_items(value: object) -> list[str]:
    """Возвращает именованные элементы."""
    if not isinstance(value, list):
        return []

    names: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        if isinstance(name, str) and name:
            names.append(name)

    return names
