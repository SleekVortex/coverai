from dataclasses import dataclass


class LLMClientError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class LLMCompletion:
    text: str
    model: str
    generation_ms: int
