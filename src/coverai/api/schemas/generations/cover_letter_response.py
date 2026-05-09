from datetime import datetime

from pydantic import BaseModel

from coverai.domain.enums import Tone


class CoverLetterResponse(BaseModel):
    id: int
    vacancy_title: str
    employer_name: str
    tone: Tone
    text: str
    model: str
    generation_ms: int
    created_at: datetime | None
