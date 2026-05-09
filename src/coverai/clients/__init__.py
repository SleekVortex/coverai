"""External API clients."""

from coverai.clients.hh import HHApiVacancySource, HHHtmlVacancySource, HttpxHHClient
from coverai.clients.llm import HttpxLLMClient
from coverai.clients.openrouter import HttpxOpenRouterClient
from coverai.clients.telegram import HttpxTelegramSender

__all__ = [
    "HttpxHHClient",
    "HHApiVacancySource",
    "HHHtmlVacancySource",
    "HttpxLLMClient",
    "HttpxOpenRouterClient",
    "HttpxTelegramSender",
]
