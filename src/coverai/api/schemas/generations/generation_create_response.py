from pydantic import BaseModel

from coverai.domain.enums import GenerationStatus, Tone


class GenerationCreateResponse(BaseModel):
    queued: bool
    user_id: int
    vacancy_url: str
    tone: Tone
    cost_credits: int
    generation_request_id: int
    status: GenerationStatus
