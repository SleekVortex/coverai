from coverai.domain.enums import Tone


def tone_from_callback(data: str | None) -> Tone:
    """Возвращает тон из callback data."""
    if data == "tone:confident":
        return Tone.CONFIDENT
    if data == "tone:concise":
        return Tone.CONCISE

    return Tone.FORMAL
