from html import unescape
from html.parser import HTMLParser


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def html_to_text(value: str) -> str:
    """Преобразует HTML в текст."""
    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return unescape(" ".join(parser.parts))


def normalize_text(value: str) -> str:
    """Нормализует текст."""
    return " ".join(value.split())


def truncate_text(value: str, max_length: int) -> str:
    """Обрезает текст."""
    if len(value) <= max_length:
        return value

    return value[: max_length - 1].rstrip() + "..."
