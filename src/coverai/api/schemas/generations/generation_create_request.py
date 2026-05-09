from pydantic import BaseModel

from coverai.domain.enums import Tone


class GenerationCreateRequest(BaseModel):
    vacancy_url: str
    tone: Tone = Tone.FORMAL
