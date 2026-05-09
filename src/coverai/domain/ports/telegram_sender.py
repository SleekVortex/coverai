from typing import Protocol, runtime_checkable


@runtime_checkable
class TelegramSender(Protocol):
    async def send_message(self, telegram_id: int, text: str) -> None:
        """Отправляет сообщение."""
        ...
