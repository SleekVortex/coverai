from dataclasses import dataclass

from coverai.domain.entities import ResumeProfile


@dataclass(frozen=True, slots=True)
class NormalizedResumeText:
    text: str
    was_truncated: bool


@dataclass(frozen=True, slots=True)
class ProfileResult:
    profile: ResumeProfile
    was_truncated: bool

