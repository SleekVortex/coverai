from datetime import UTC, datetime
from pathlib import Path

from aiogram import Bot
from arq.connections import ArqRedis
from dishka import AsyncContainer, Scope
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from coverai.configs import get_settings
from coverai.di.container import create_di_container
from coverai.domain.entities import CoverLetter, ResumeProfile, User
from coverai.domain.enums import GenerationStatus, Tone
from coverai.infra.db import models
from coverai.infra.db.session import session_scope
from coverai.infra.metrics import prometheus_metrics
from coverai.repos.sqlalchemy import (
    CoverLetterSqlAlchemyRepo,
    GenerationRequestSqlAlchemyRepo,
    ResumeProfileSqlAlchemyRepo,
    SubscriptionSqlAlchemyRepo,
    UserSqlAlchemyRepo,
)
from coverai.services.billing import PlanUsage, QuotaService
from coverai.services.billing.errors import InsufficientCreditsError, QuotaExceededError
from coverai.services.history import HistoryResult, HistoryService
from coverai.services.profile import ProfileResult, ProfileService
from coverai.services.profile.errors import ProfileAlreadyExistsError
from coverai.services.resume_files import ResumeFileTextExtractor, ResumeTextExtractor
from coverai.services.resume_files.errors import ResumeTextNotExtractedError
from coverai.services.users import UserRegistrationService


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

    async def get_or_create_user(
        self,
        telegram_id: int,
        username: str | None,
        first_name: str | None,
        language_code: str | None,
    ) -> User:
        """Возвращает или создает пользователя."""
        async with (
            session_scope(self._session_factory) as session,
            self._di_container(
                {AsyncSession: session},
                scope=Scope.REQUEST,
            ) as request_scope,
        ):
            service = await request_scope.get(UserRegistrationService)
            return await service.get_or_create_telegram_user(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                language_code=language_code,
            )

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        container = self._di_container
        if isinstance(container, AsyncContainer):
            await container.close()

    async def save_resume_text(self, user_id: int, resume_text: str) -> ProfileResult:
        """Сохраняет текст резюме."""
        async with session_scope(self._session_factory) as session:
            profile_service = ProfileService(ResumeProfileSqlAlchemyRepo(session))
            try:
                return await profile_service.create_profile(
                    user_id=user_id,
                    title="Resume",
                    resume_text=resume_text,
                )
            except ProfileAlreadyExistsError:
                return await profile_service.update_profile(user_id, resume_text)

    async def save_resume_file(
        self,
        user_id: int,
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
        async with session_scope(self._session_factory) as session:
            profile_service = ProfileService(ResumeProfileSqlAlchemyRepo(session))
            try:
                return await profile_service.create_profile(
                    user_id=user_id,
                    title=_resume_title_from_filename(file_name),
                    resume_text=text,
                )
            except ProfileAlreadyExistsError:
                return await profile_service.update_profile(user_id, text)

    async def get_profile(self, user_id: int) -> ResumeProfile:
        """Возвращает профиль."""
        async with session_scope(self._session_factory) as session:
            profile_service = ProfileService(ResumeProfileSqlAlchemyRepo(session))
            return await profile_service.get_profile(user_id)

    async def get_plan_usage(self, user_id: int) -> PlanUsage:
        """Возвращает использование тарифа."""
        async with session_scope(self._session_factory) as session:
            user_repo = UserSqlAlchemyRepo(session)
            subscription_repo = SubscriptionSqlAlchemyRepo(session)
            request_repo = GenerationRequestSqlAlchemyRepo(session)
            return await QuotaService(
                user_repo=user_repo,
                subscription_repo=subscription_repo,
                generation_request_repo=request_repo,
                metrics=prometheus_metrics,
            ).get_plan_usage(user_id)

    async def get_credit_balance(self, user_id: int) -> int:
        """Возвращает баланс кредитов."""
        async with session_scope(self._session_factory) as session:
            user = await session.get(models.User, user_id)
            return int(user.credits) if user is not None else 0

    async def redeem_promo_code(self, user_id: int, code: str) -> str:
        """Активирует промокод."""
        normalized = code.strip().upper()
        async with session_scope(self._session_factory) as session:
            promo = await session.scalar(
                select(models.PromoCode)
                .where(models.PromoCode.code == normalized)
                .with_for_update(),
            )
            if promo is None:
                return "Промокод не найден."

            existing = await session.scalar(
                select(models.PromoRedemption).where(
                    models.PromoRedemption.promo_code_id == promo.id,
                    models.PromoRedemption.user_id == user_id,
                ),
            )
            if existing is not None:
                return "Вы уже активировали этот промокод."

            user = await session.scalar(
                select(models.User).where(models.User.id == user_id).with_for_update(),
            )
            if user is None:
                return "Пользователь не найден."

            promo.activations_count += 1
            session.add(
                models.PromoRedemption(promo_code_id=promo.id, user_id=user_id),
            )
            if promo.type == "fixed_credits":
                user.credits += promo.value
                session.add(
                    models.CreditTransaction(
                        user_id=user_id,
                        type="promo",
                        amount=promo.value,
                        balance_after=user.credits,
                        description=f"Telegram promo {promo.code}",
                        promo_code_id=promo.id,
                    ),
                )
                return f"Промокод активирован. Баланс: {user.credits} кредитов."

            user.pending_top_up_discount_percent = promo.value
            return f"Скидка {promo.value}% применится к следующему пополнению."

    async def create_mock_top_up(self, user_id: int, credits_amount: int) -> str:
        """Создает mock-пополнение."""
        async with session_scope(self._session_factory) as session:
            user = await session.scalar(
                select(models.User).where(models.User.id == user_id).with_for_update(),
            )
            if user is None:
                return "Пользователь не найден."

            discount = user.pending_top_up_discount_percent
            amount_rub = (
                credits_amount
                * self._settings.billing.credit_price_rub
                * (100 - discount)
                // 100
            )
            user.credits += credits_amount
            user.pending_top_up_discount_percent = 0
            payment = models.PaymentIntent(
                user_id=user_id,
                credits_amount=credits_amount,
                amount_rub=amount_rub,
                discount_percent=discount,
                status="succeeded",
                provider="telegram_mock",
                external_id=f"telegram_mock_{user_id}_{credits_amount}",
            )
            session.add(payment)
            await session.flush()
            session.add(
                models.CreditTransaction(
                    user_id=user_id,
                    type="top_up",
                    amount=credits_amount,
                    balance_after=user.credits,
                    description="Telegram mock top-up",
                    payment_intent_id=payment.id,
                ),
            )
            return (
                f"Баланс пополнен на {credits_amount} кредитов.\n"
                f"Списано по mock-платежу: {amount_rub} ₽.\n"
                f"Текущий баланс: {user.credits} кредитов."
            )

    async def list_history(self, user_id: int) -> HistoryResult:
        """Возвращает историю писем."""
        async with session_scope(self._session_factory) as session:
            return await HistoryService(
                user_repo=UserSqlAlchemyRepo(session),
                cover_letter_repo=CoverLetterSqlAlchemyRepo(session),
            ).list_history(user_id)

    async def get_history_letter(self, user_id: int, letter_id: int) -> CoverLetter:
        """Возвращает письмо из истории."""
        async with session_scope(self._session_factory) as session:
            return await HistoryService(
                user_repo=UserSqlAlchemyRepo(session),
                cover_letter_repo=CoverLetterSqlAlchemyRepo(session),
            ).get_letter(user_id, letter_id)

    async def enqueue_generation(
        self,
        user_id: int,
        vacancy_url: str,
        tone: Tone,
    ) -> None:
        """Ставит генерацию в очередь."""
        cost_credits = self._settings.billing.prediction_cost_credits
        async with session_scope(self._session_factory) as session:
            user = await session.get(models.User, user_id)
            if user is None or user.credits < cost_credits:
                raise InsufficientCreditsError
            existing_requests = await GenerationRequestSqlAlchemyRepo(
                session,
            ).count_by_user_statuses_since(
                user_id=user_id,
                statuses={GenerationStatus.PENDING, GenerationStatus.SUCCEEDED},
                since=datetime.now(UTC).replace(
                    hour=0,
                    minute=0,
                    second=0,
                    microsecond=0,
                ),
            )
            if user.plan == "free" and existing_requests >= 1:
                raise QuotaExceededError

        await self._arq_pool.enqueue_job(
            "generate_cover_letter",
            user_id,
            vacancy_url,
            tone.value,
            True,
            True,
            cost_credits,
        )


def _resume_title_from_filename(file_name: str) -> str:
    title = Path(file_name).stem.strip()
    return title or "Resume"
