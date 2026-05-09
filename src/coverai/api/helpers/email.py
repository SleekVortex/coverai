def normalize_email(email: str) -> str:
    """Нормализует email."""
    return email.strip().lower()


def is_valid_email(email: str) -> bool:
    """Проверяет формат email."""
    return "@" in email and "." in email.rsplit("@", 1)[-1]
