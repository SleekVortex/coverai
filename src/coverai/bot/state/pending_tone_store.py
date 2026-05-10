class PendingToneStore:
    def __init__(self) -> None:
        self._vacancy_urls: dict[int, str] = {}

    def set(self, telegram_id: int, vacancy_url: str) -> None:
        """Сохраняет значение."""
        self._vacancy_urls[telegram_id] = vacancy_url

    def pop(self, telegram_id: int) -> str | None:
        """Извлекает и удаляет значение."""
        return self._vacancy_urls.pop(telegram_id, None)
