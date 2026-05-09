from pydantic import BaseModel


class ProfileResponse(BaseModel):
    id: int
    title: str
    resume_text: str
    was_truncated: bool = False
