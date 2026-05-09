from pydantic import BaseModel


class ProfileRequest(BaseModel):
    title: str = "Resume"
    resume_text: str
