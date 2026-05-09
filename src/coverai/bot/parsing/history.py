def history_letter_id(text: str | None) -> int | None:
    """Извлекает id письма из команды."""
    if text is None:
        return None

    parts = text.split(maxsplit=1)
    if len(parts) != 2 or not parts[1].strip().isdecimal():
        return None

    return int(parts[1].strip())
