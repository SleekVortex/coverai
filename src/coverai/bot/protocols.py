from typing import Protocol

from coverai.domain.entities import CoverLetter, ResumeProfile, User
from coverai.domain.enums import Tone
from coverai.services.billing import PlanUsage
from coverai.services.history import HistoryResult
from coverai.services.profile import ProfileResult


class TelegramUser(Protocol):
    id: int
    username: str | None
    first_name: str | None
    language_code: str | None


class TelegramDocument(Protocol):
    file_id: str
    file_name: str | None


class IncomingMessage(Protocol):
    from_user: TelegramUser | None
    text: str | None
    document: TelegramDocument | None

    async def answer(
        self,
        text: str,
        reply_markup: object | None = None,
    ) -> object:
        """Отправляет ответ пользователю."""
        ...


class IncomingCallback(Protocol):
    from_user: TelegramUser
    data: str | None
    message: IncomingMessage | None

    async def answer(
        self,
        text: str | None = None,
        show_alert: bool | None = None,
    ) -> object:
        """Отправляет ответ пользователю."""
        ...


class BotUseCases(Protocol):
    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language_code: str | None,
    ) -> User:
        """Возвращает или создает пользователя."""
        ...

    async def save_resume_text(
        self, user_id: int, resume_text: str
    ) -> ProfileResult:
        """Сохраняет текст резюме."""
        ...

    async def save_resume_file(
        self,
        user_id: int,
        file_id: str,
        file_name: str,
    ) -> ProfileResult:
        """Сохраняет резюме из файла."""
        ...

    async def get_profile(self, user_id: int) -> ResumeProfile:
        """Возвращает профиль."""
        ...

    async def get_plan_usage(self, user_id: int) -> PlanUsage:
        """Возвращает использование тарифа."""
        ...

    async def get_credit_balance(self, user_id: int) -> int:
        """Возвращает баланс кредитов."""
        ...

    async def redeem_promo_code(self, user_id: int, code: str) -> str:
        """Активирует промокод."""
        ...

    async def create_mock_top_up(self, user_id: int, credits_amount: int) -> str:
        """Создает mock-пополнение."""
        ...

    async def list_history(self, user_id: int) -> HistoryResult:
        """Возвращает историю писем."""
        ...

    async def get_history_letter(self, user_id: int, letter_id: int) -> CoverLetter:
        """Возвращает письмо из истории."""
        ...

    async def enqueue_generation(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
    ) -> None:
        """Ставит генерацию в очередь."""
        ...
