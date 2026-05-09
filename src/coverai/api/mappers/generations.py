from typing import Any

from coverai.api.helpers.ids import required_id
from coverai.api.schemas import CoverLetterResponse, GenerationStatusResponse


def letter_response(letter: Any) -> CoverLetterResponse:
    """Преобразует письмо в API response."""
    return CoverLetterResponse(
        id=letter.id or 0,
        vacancy_title=letter.vacancy_title,
        employer_name=letter.employer_name,
        tone=letter.tone,
        text=letter.text,
        model=letter.model,
        generation_ms=letter.generation_ms,
        created_at=letter.created_at,
    )


def generation_status_response(generation_request: Any) -> GenerationStatusResponse:
    """Преобразует статус генерации в response."""
    return GenerationStatusResponse(
        id=required_id(generation_request),
        status=generation_request.status,
        tone=generation_request.tone,
        error_message=generation_request.error_message,
        completed_at=generation_request.completed_at,
    )
