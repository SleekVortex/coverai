from typing import Protocol


class ResumeTextExtractor(Protocol):
    def extract_text(self, file_name: str, content: bytes) -> str:
        """Извлекает текст."""
        ...

