from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from aiogram import Bot
from arq.connections import ArqRedis
from dishka import AsyncContainer, Scope
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from coverai.configs import get_settings
from coverai.di.container import create_di_container
from coverai.domain.entities import CoverLetter, ResumeProfile, User
from coverai.domain.enums import PromoCodeType, Tone
from coverai.domain.generation_job_queue import GenerationJobQueue
from coverai.domain.ids import required_id
from coverai.domain.ports import BillingReadRepo
from coverai.infra.arq_generation_job_queue import ArqGenerationJobQueue
from coverai.infra.db.session import session_scope
from coverai.services.billing import (
    PaymentService,
    PlanUsage,
    PromoService,
    QuotaService,
)
from coverai.services.billing.errors import (
    PaymentNotFoundError,
    PromoCodeAlreadyRedeemedError,
    PromoCodeInvalidError,
    PromoCodeNotFoundError,
)
from coverai.services.generation import GenerationQueueService
from coverai.services.history import HistoryResult, HistoryService
from coverai.services.profile import ProfileResult, ProfileService
from coverai.services.profile.errors import ProfileAlreadyExistsError
from coverai.services.resume_files import ResumeFileTextExtractor, ResumeTextExtractor
from coverai.services.resume_files.errors import ResumeTextNotExtractedError
from coverai.services.users import UserRegistrationService
from coverai.services.users.errors import UserNotFoundError


class RuntimeBotUseCases:
    def __init__(
        self,
        bot: Bot,
        session_factory: async_sessionmaker[AsyncSession],
        arq_pool: ArqRedis,
        resume_extractor: ResumeTextExtractor | None = None,
    ) -> None:
        self._bot = bot
        self._session_factory = session_factory
        self._arq_pool = arq_pool
        self._resume_extractor = resume_extractor or ResumeFileTextExtractor()
        self._settings = get_settings()
        self._di_container = create_di_container(self._settings)

    @asynccontextmanager
    async def _request_scope(
        self,
        queue: GenerationJobQueue | None = None,
    ) -> AsyncIterator[AsyncContainer]:
        context: dict[object, object] = {}
        async with session_scope(self._session_factory) as session:
            context[AsyncSession] = session
            if queue is not None:
                context[GenerationJobQueue] = queue
            async with self._di_container(
                context,
                scope=Scope.REQUEST,
            ) as request_scope:
                yield request_scope

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language_code: str | None,
    ) -> User:
        """Возвращает или создает пользователя."""
        async with self._request_scope() as request_scope:
            service = await request_scope.get(UserRegistrationService)
            return await service.get_or_create_telegram_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language_code=language_code,
            )

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        await self._di_container.close()

    async def save_resume_text(self, user: User, resume_text: str) -> ProfileResult:
        """Сохраняет текст резюме."""
        async with self._request_scope() as request_scope:
            profile_service = await request_scope.get(ProfileService)
            try:
                return await profile_service.create_profile_for_user(
                    user=user,
                    title="Resume",
                    resume_text=resume_text,
                )
            except ProfileAlreadyExistsError:
                return await profile_service.update_profile_for_user(
                    user,
                    resume_text,
                )

    async def save_resume_file(
        self,
        user: User,
        file_id: str,
        file_name: str,
    ) -> ProfileResult:
        """Сохраняет резюме из файла."""
        file = await self._bot.get_file(file_id)
        if file.file_path is None:
            raise ResumeTextNotExtractedError

        downloaded = await self._bot.download_file(file.file_path)
        if downloaded is None:
            raise ResumeTextNotExtractedError

        content = downloaded.read()
        text = self._resume_extractor.extract_text(file_name, content)
        async with self._request_scope() as request_scope:
            profile_service = await request_scope.get(ProfileService)
            try:
                return await profile_service.create_profile_for_user(
                    user=user,
                    title=_resume_title_from_filename(file_name),
                    resume_text=text,
                )
            except ProfileAlreadyExistsError:
                return await profile_service.update_profile_for_user(user, text)

    async def get_profile(self, user: User) -> ResumeProfile:
        """Возвращает профиль."""
        async with self._request_scope() as request_scope:
            profile_service = await request_scope.get(ProfileService)
            return await profile_service.get_profile_for_user(user)

    async def get_plan_usage(self, user: User) -> PlanUsage:
        """Возвращает использование тарифа."""
        async with self._request_scope() as request_scope:
            quota_service = await request_scope.get(QuotaService)
            return await quota_service.get_plan_usage_for_user(user)

    async def get_credit_balance(self, user: User) -> int:
        """Возвращает баланс кредитов."""
        async with self._request_scope() as request_scope:
            read_repo = await request_scope.get(BillingReadRepo)
            summary = await read_repo.billing_summary(required_id(user), recent_limit=0)
            return summary.credits

    async def redeem_promo_code(self, user: User, code: str) -> str:
        """Активирует промокод."""
        async with self._request_scope() as request_scope:
            promo_service = await request_scope.get(PromoService)
            try:
                result = await promo_service.redeem(user, code)
            except PromoCodeNotFoundError:
                return "Промокод не найден."
            except PromoCodeAlreadyRedeemedError:
                return "Вы уже активировали этот промокод."
            except PromoCodeInvalidError:
                return "Промокод недоступен."

            if result.promo.type == PromoCodeType.FIXED_CREDITS:
                read_repo = await request_scope.get(BillingReadRepo)
                summary = await read_repo.billing_summary(
                    required_id(user),
                    recent_limit=0,
                )
                return f"Промокод активирован. Баланс: {summary.credits} кредитов."

            return f"Скидка {result.promo.value}% применится к следующему пополнению."

    async def create_mock_top_up(self, user: User, credits_amount: int) -> str:
        """Создает mock-пополнение."""
        async with self._request_scope() as request_scope:
            payment_service = await request_scope.get(PaymentService)
            try:
                intent = await payment_service.create_top_up(user, credits_amount)
                confirmed = await payment_service.confirm(intent.external_id)
            except (PaymentNotFoundError, UserNotFoundError):
                return "Пользователь не найден."

            read_repo = await request_scope.get(BillingReadRepo)
            summary = await read_repo.billing_summary(required_id(user), recent_limit=0)
            return (
                f"Баланс пополнен на {confirmed.credits_amount} кредитов.\n"
                f"Списано по mock-платежу: {confirmed.amount_rub} ₽.\n"
                f"Текущий баланс: {summary.credits} кредитов."
            )

    async def list_history(self, user: User) -> HistoryResult:
        """Возвращает историю писем."""
        async with self._request_scope() as request_scope:
            history_service = await request_scope.get(HistoryService)
            return await history_service.list_history_for_user(user)

    async def get_history_letter(self, user: User, letter_id: int) -> CoverLetter:
        """Возвращает письмо из истории."""
        async with self._request_scope() as request_scope:
            history_service = await request_scope.get(HistoryService)
            return await history_service.get_letter_for_user(user, letter_id)

    async def enqueue_generation(
        self,
        user: User,
        vacancy_url: str,
        tone: Tone,
    ) -> None:
        """Ставит генерацию в очередь."""
        queue = ArqGenerationJobQueue(
            self._arq_pool,
            notify_telegram=True,
        )
        async with self._request_scope(queue=queue) as request_scope:
            service = await request_scope.get(GenerationQueueService)
            await service.enqueue_generation_for_user(user, vacancy_url, tone)


def _resume_title_from_filename(file_name: str) -> str:
    title = Path(file_name).stem.strip()
    return title or "Resume"
