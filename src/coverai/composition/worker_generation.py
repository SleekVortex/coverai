from typing import cast

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from coverai.clients.hh import HttpxHHClient
from coverai.clients.llm import HttpxLLMClient
from coverai.clients.telegram import HttpxTelegramSender
from coverai.configs import Settings
from coverai.domain.credit_transaction import CreditTransaction
from coverai.domain.enums import CreditTransactionType, Tone
from coverai.domain.hh import HHClientError
from coverai.infra.db.session import session_scope
from coverai.infra.metrics import prometheus_metrics
from coverai.repos.credit_ledger_sqlalchemy import CreditLedgerSqlAlchemyRepo
from coverai.repos.sqlalchemy import (
    CoverLetterSqlAlchemyRepo,
    GenerationRequestSqlAlchemyRepo,
    ResumeProfileSqlAlchemyRepo,
    SubscriptionSqlAlchemyRepo,
    UserSqlAlchemyRepo,
    VacancySqlAlchemyRepo,
)
from coverai.services.billing import QuotaService
from coverai.services.billing.errors import QuotaExceededError
from coverai.services.generation import CoverLetterService
from coverai.services.vacancy import VacancyService

HH_CLIENT_ERROR_MESSAGE = (
    "⚠️ Не удалось загрузить вакансию с hh.ru\n\n"
    "Попробуйте позже или отправьте другую ссылку."
)
QUOTA_EXCEEDED_MESSAGE = (
    "⚠️ Лимит тарифа исчерпан\n\nПроверьте 📊 Мой лимит или откройте 💳 Тарифы."
)


async def generate_cover_letter_job(
    ctx: dict[str, object],
    user_id: int,
    vacancy_url: str,
    tone: str,
    notify_telegram: bool,
    charge_credits: bool,
    cost_credits: int,
    generation_request_id: int | None,
) -> int:
    """Runs one cover-letter generation job with an arq job scope."""
    settings = context_value(ctx, "settings", Settings)
    session_factory = session_factory_from_context(ctx)

    hh_client = HttpxHHClient(
        access_token=settings.hh.access_token,
        user_agent=settings.hh.user_agent,
        proxy_url=settings.hh.proxy_url,
        html_fallback_enabled=settings.hh.html_fallback_enabled,
    )
    llm_client = HttpxLLMClient(
        api_key=settings.llm.api_key,
        model=settings.llm.model,
        base_url=settings.llm.base_url,
        proxy_url=settings.llm.proxy_url,
    )
    telegram_sender = (
        HttpxTelegramSender(
            settings.telegram.bot_token,
            proxy_url=settings.telegram.proxy_url,
        )
        if notify_telegram
        else None
    )
    telegram_id: int | None = None
    text: str | None = None
    letter_id: int | None = None
    hh_error: HHClientError | None = None
    quota_error: QuotaExceededError | None = None

    try:
        async with session_scope(session_factory) as session:
            user_repo = UserSqlAlchemyRepo(session)
            profile_repo = ResumeProfileSqlAlchemyRepo(session)
            request_repo = GenerationRequestSqlAlchemyRepo(session)
            letter_repo = CoverLetterSqlAlchemyRepo(session)
            vacancy_repo = VacancySqlAlchemyRepo(session)
            subscription_repo = SubscriptionSqlAlchemyRepo(session)
            credit_ledger_repo = CreditLedgerSqlAlchemyRepo(session)

            quota_service = QuotaService(
                user_repo=user_repo,
                subscription_repo=subscription_repo,
                generation_request_repo=request_repo,
                metrics=prometheus_metrics,
            )
            vacancy_service = VacancyService(
                vacancy_repo=vacancy_repo,
                hh_client=hh_client,
                metrics=prometheus_metrics,
            )
            cover_letter_service = CoverLetterService(
                user_repo=user_repo,
                profile_repo=profile_repo,
                generation_request_repo=request_repo,
                cover_letter_repo=letter_repo,
                vacancy_service=vacancy_service,
                quota_service=quota_service,
                llm_client=llm_client,
                metrics=prometheus_metrics,
            )

            try:
                result = await cover_letter_service.generate_for_vacancy_url(
                    user_id=user_id,
                    vacancy_url=vacancy_url,
                    tone=Tone(tone),
                    generation_request_id=generation_request_id,
                    enforce_quota=generation_request_id is None,
                )
            except HHClientError as error:
                user = await user_repo.get_by_id(user_id)
                telegram_id = user.telegram_id if user is not None else None
                hh_error = error
            except QuotaExceededError as error:
                user = await user_repo.get_by_id(user_id)
                telegram_id = user.telegram_id if user is not None else None
                quota_error = error
            else:
                telegram_id = result.user.telegram_id
                text = result.letter.text
                letter_id = result.letter.id
                if charge_credits and cost_credits > 0:
                    await debit_generation_credits(
                        user_repo=user_repo,
                        credit_ledger_repo=credit_ledger_repo,
                        user_id=user_id,
                        amount=cost_credits,
                        generation_request_id=result.letter.generation_request_id,
                    )

        if hh_error is not None:
            if telegram_sender is not None and telegram_id is not None:
                await telegram_sender.send_message(telegram_id, HH_CLIENT_ERROR_MESSAGE)
            raise hh_error

        if quota_error is not None:
            if telegram_sender is not None and telegram_id is not None:
                await telegram_sender.send_message(telegram_id, QUOTA_EXCEEDED_MESSAGE)
            raise quota_error

        if telegram_id is None or text is None:
            if not notify_telegram and letter_id is not None:
                return letter_id
            raise RuntimeError("cover letter generation did not produce a message")

        if telegram_sender is not None:
            await telegram_sender.send_message(telegram_id, text)
        if letter_id is None:
            raise ValueError("cover letter id is not assigned")

        return letter_id
    finally:
        await hh_client.aclose()
        await llm_client.aclose()
        if telegram_sender is not None:
            await telegram_sender.aclose()


async def debit_generation_credits(
    user_repo: UserSqlAlchemyRepo,
    credit_ledger_repo: CreditLedgerSqlAlchemyRepo,
    user_id: int,
    amount: int,
    generation_request_id: int,
) -> None:
    """Atomically debits credits for a successful generation."""
    user = await user_repo.get_by_id_for_update(user_id)
    if user is None or user.credits < amount:
        raise QuotaExceededError

    updated = await user_repo.update_credits(user_id, user.credits - amount)
    if updated is None:
        raise QuotaExceededError

    await credit_ledger_repo.record_transaction(
        CreditTransaction(
            user_id=user_id,
            type=CreditTransactionType.SPEND,
            amount=-amount,
            balance_after=updated.credits,
            description="Successful LLM cover letter generation",
            generation_request_id=generation_request_id,
        ),
    )


def context_value[T](ctx: dict[str, object], key: str, expected_type: type[T]) -> T:
    """Возвращает значение из context."""
    value = ctx.get(key)
    if not isinstance(value, expected_type):
        raise RuntimeError(f"worker context misses {key}")

    return value


def session_factory_from_context(
    ctx: dict[str, object],
) -> async_sessionmaker[AsyncSession]:
    """Возвращает фабрику сессий из context."""
    value = ctx.get("session_factory")
    if not isinstance(value, async_sessionmaker):
        raise RuntimeError("worker context misses session_factory")

    return cast("async_sessionmaker[AsyncSession]", value)
