from datetime import datetime

from pydantic import BaseModel

from coverai.domain.enums import GenerationStatus, Tone


class GenerationStatusResponse(BaseModel):
    id: int
    status: GenerationStatus
    tone: Tone
    error_message: str | None = None
    completed_at: datetime | None = None
