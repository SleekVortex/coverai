from dataclasses import dataclass

from coverai.domain.entities import CoverLetter, User


@dataclass(frozen=True, slots=True)
class GeneratedCoverLetter:
    user: User
    letter: CoverLetter

