import httpx


class TelegramSenderError(Exception):
    pass


class HttpxTelegramSender:
    def __init__(
        self,
        bot_token: str,
        proxy_url: str = "",
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        if not bot_token:
            raise TelegramSenderError("Telegram bot token is empty")

        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=f"https://api.telegram.org/bot{bot_token}",
            proxy=proxy_url or None,
            timeout=15.0,
        )

    async def send_message(self, telegram_id: int, text: str) -> None:
        """Отправляет сообщение."""
        try:
            response = await self._client.post(
                "/sendMessage",
                json={"chat_id": telegram_id, "text": text},
            )
        except httpx.HTTPError as error:
            raise TelegramSenderError(str(error)) from error

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise TelegramSenderError(str(error)) from error

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        if self._owns_client:
            await self._client.aclose()
