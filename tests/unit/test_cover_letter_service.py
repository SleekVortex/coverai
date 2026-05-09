import pytest
from fakes.repos import (
    FakeCoverLetterRepo,
    FakeGenerationRequestRepo,
    FakeResumeProfileRepo,
    FakeSubscriptionRepo,
    FakeUserRepo,
    FakeVacancyRepo,
)

from coverai.domain.entities import Employer, ResumeProfile, User, Vacancy
from coverai.domain.enums import GenerationStatus, Plan, Tone
from coverai.domain.hh import HHClientError, HHEmployerPayload, HHVacancyPayload
from coverai.domain.llm import LLMClientError, LLMCompletion
from coverai.services.billing import QuotaService
from coverai.services.generation import CoverLetterService
from coverai.services.generation.errors import EmptyLLMResponseError
from coverai.services.prompts import build_cover_letter_prompt
from coverai.services.vacancy import VacancyService


class FakeOpenRouterClient:
    def __init__(
        self,
        text: str = "Здравствуйте! Хочу откликнуться на вакансию.",
        error: Exception | None = None,
    ) -> None:
        self._text = text
        self._error = error
        self.prompts: list[str] = []

    async def generate_cover_letter(self, prompt: str) -> LLMCompletion:
        self.prompts.append(prompt)
        if self._error is not None:
            raise self._error

        return LLMCompletion(
            text=self._text,
            model="test-model",
            generation_ms=123,
        )


class FakeHHClient:
    def __init__(self, error: Exception | None = None) -> None:
        self._error = error

    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        if self._error is not None:
            raise self._error

        return HHVacancyPayload(
            hh_id=hh_id,
            title="Python Developer",
            employer_hh_id=456,
            employer_name="Example LLC",
            url=f"https://hh.ru/vacancy/{hh_id}",
            archived=False,
            type_id="open",
            raw_payload={"id": str(hh_id)},
        )

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        return HHEmployerPayload(
            hh_id=hh_id,
            name="Example LLC",
            url="https://hh.ru/employer/456",
            raw_payload={"id": str(hh_id)},
        )


class CoverLetterFixture:
    def __init__(
        self,
        llm_client: FakeOpenRouterClient | None = None,
        hh_client: FakeHHClient | None = None,
    ) -> None:
        self.user_repo = FakeUserRepo()
        self.profile_repo = FakeResumeProfileRepo()
        self.request_repo = FakeGenerationRequestRepo()
        self.letter_repo = FakeCoverLetterRepo()
        self.vacancy_repo = FakeVacancyRepo()
        self.subscription_repo = FakeSubscriptionRepo()
        self.llm_client = llm_client or FakeOpenRouterClient()
        self.hh_client = hh_client or FakeHHClient()
        self.quota_service = QuotaService(
            user_repo=self.user_repo,
            subscription_repo=self.subscription_repo,
            generation_request_repo=self.request_repo,
        )
        self.service = CoverLetterService(
            user_repo=self.user_repo,
            profile_repo=self.profile_repo,
            generation_request_repo=self.request_repo,
            cover_letter_repo=self.letter_repo,
            vacancy_service=VacancyService(
                vacancy_repo=self.vacancy_repo,
                hh_client=self.hh_client,
            ),
            quota_service=self.quota_service,
            llm_client=self.llm_client,
        )


@pytest.mark.asyncio
async def test_cover_letter_generation_happy_path() -> None:
    fixture = CoverLetterFixture()
    user = await create_user_with_profile(fixture)

    result = await fixture.service.generate_for_vacancy_url(
        user_id=required_id(user),
        vacancy_url="https://hh.ru/vacancy/123",
        tone=Tone.CONCISE,
    )

    assert result.user.telegram_id == user.telegram_id
    assert result.letter.text == "Здравствуйте! Хочу откликнуться на вакансию."
    assert result.letter.model == "test-model"
    assert result.letter.generation_ms == 123
    assert len(fixture.letter_repo.letters) == 1
    request = only(list(fixture.request_repo.requests.values()))
    assert request.status == GenerationStatus.SUCCEEDED
    assert "Не добавляй факты о кандидате" in fixture.llm_client.prompts[0]
    assert "plain text" in fixture.llm_client.prompts[0]


@pytest.mark.asyncio
async def test_empty_llm_response_marks_request_failed() -> None:
    fixture = CoverLetterFixture(llm_client=FakeOpenRouterClient(text=" "))
    user = await create_user_with_profile(fixture)

    with pytest.raises(EmptyLLMResponseError):
        await fixture.service.generate_for_vacancy_url(
            user_id=required_id(user),
            vacancy_url="https://hh.ru/vacancy/123",
        )

    assert fixture.letter_repo.letters == {}
    request = only(list(fixture.request_repo.requests.values()))
    assert request.status == GenerationStatus.FAILED
    assert request.error_message == "EmptyLLMResponseError"
    usage = await fixture.quota_service.get_plan_usage(required_id(user))
    assert usage.used == 0


@pytest.mark.asyncio
async def test_llm_timeout_marks_request_failed() -> None:
    fixture = CoverLetterFixture(
        llm_client=FakeOpenRouterClient(error=LLMClientError("timeout")),
    )
    user = await create_user_with_profile(fixture)

    with pytest.raises(LLMClientError):
        await fixture.service.generate_for_vacancy_url(
            user_id=required_id(user),
            vacancy_url="https://hh.ru/vacancy/123",
        )

    assert fixture.letter_repo.letters == {}
    request = only(list(fixture.request_repo.requests.values()))
    assert request.status == GenerationStatus.FAILED
    assert request.error_message == "timeout"
    usage = await fixture.quota_service.get_plan_usage(required_id(user))
    assert usage.used == 0


@pytest.mark.asyncio
async def test_hh_failure_does_not_create_letter_or_spend_quota() -> None:
    fixture = CoverLetterFixture(
        hh_client=FakeHHClient(error=HHClientError("hh.ru unavailable")),
    )
    user = await create_user_with_profile(fixture)

    with pytest.raises(HHClientError):
        await fixture.service.generate_for_vacancy_url(
            user_id=required_id(user),
            vacancy_url="https://hh.ru/vacancy/123",
        )

    assert fixture.request_repo.requests == {}
    assert fixture.letter_repo.letters == {}
    usage = await fixture.quota_service.get_plan_usage(required_id(user))
    assert usage.used == 0


def test_prompt_forbids_invented_experience_and_limits_format() -> None:
    prompt = build_cover_letter_prompt(
        profile=ResumeProfile(
            id=1,
            user_id=1,
            resume_text="Python developer with FastAPI and PostgreSQL experience.",
        ),
        vacancy=Vacancy(
            id=2,
            hh_id=123,
            employer_id=3,
            title="Backend Developer",
            url="https://hh.ru/vacancy/123",
            raw_payload={
                "description": "<p>Build APIs and async workers.</p>",
                "key_skills": [{"name": "FastAPI"}, {"name": "PostgreSQL"}],
                "experience": {"name": "3-6 years"},
                "employment": {"name": "Full time"},
                "schedule": {"name": "Remote"},
            },
        ),
        employer=Employer(
            id=3,
            hh_id=456,
            name="Example LLC",
        ),
        tone=Tone.FORMAL,
    )

    assert "plain text" in prompt
    assert "Без Markdown" in prompt
    assert "подписи, контактов и плейсхолдеров" in prompt
    assert "Начни письмо с приветствия" in prompt
    assert "Добрый день" in prompt
    assert "Если текст вакансии неформальный" in prompt
    assert "Привет" in prompt
    assert "без канцелярита" in prompt
    assert "Творчески работай только с подачей" in prompt
    assert "не упоминай резюме как документ" in prompt
    assert "упомяни название вакансии и работодателя" in prompt
    assert "если известно название работодателя" in prompt
    assert "где кандидат будет полезен" in prompt
    assert "Не пересказывай резюме" in prompt
    assert "Не пиши мета-фразы" in prompt
    assert "в описании вакансии" in prompt
    assert "из резюме видно" in prompt
    assert "Не копируй пункты" in prompt
    assert "Не перечисляй стек или задачи через запятую" in prompt
    assert "перефразируй их как рабочую ситуацию" in prompt
    assert "1-2 осмысленных рабочих сценария" in prompt
    assert "почему кандидату интересны именно они" in prompt
    assert "Мотивация к компании" in prompt
    assert "продукт, домен, аудиторию" in prompt
    assert "Не пиши общие фразы вроде" in prompt
    assert "Если конкретики про продукт или компанию нет" in prompt
    assert "знаком с продуктом" in prompt
    assert "сам им пользуется" in prompt
    assert "Не выдумывай знакомство с продуктом" in prompt
    assert "отвечает человеку" in prompt
    assert "Не делай шаблонное письмо" in prompt
    assert "Не повторяй структуру примеров" in prompt
    assert "Слово 'готов' допустимо" in prompt
    assert "Не строй каждый абзац по шаблону" in prompt
    assert "Не используй клише" in prompt
    assert "интересен мне именно как продукт" in prompt
    assert "не абстрактно" in prompt
    assert "Избегай парных шаблонных оборотов" in prompt
    assert "Собери письмо вокруг 1-2 сильных задач" in prompt
    assert "что нужно работодателю" in prompt
    assert "Финал должен быть уверенным call to action" in prompt
    assert "обсудить контекст" in prompt
    assert "ожидания от роли" in prompt
    assert "Не предлагай готовые решения" in prompt
    assert "до знакомства со спецификой проекта" in prompt
    assert "задать правильные вопросы" in prompt
    assert "формат интервью" in prompt
    assert "готов пообщаться на интервью" in prompt
    assert "Не заканчивай каждое письмо фразой" in prompt
    assert "разрабатывать, дорабатывать, интегрировать" in prompt
    assert "Не добавляй факты о кандидате" in prompt
    assert "Не заявляй достижений, метрик или оптимизаций" in prompt
    assert "Не приписывай кандидату требования" in prompt
    assert "Примеры хорошего стиля" in prompt
    assert "Не копируй из примеров факты" in prompt
    assert "Названия компаний и продуктов в примерах условные" in prompt
    assert "Пример 1" in prompt
    assert "Пример 5" in prompt
    assert "Пример 6" not in prompt
    assert "Привет." in prompt
    assert "PlatformPay" in prompt
    assert "платежных сервисах" in prompt
    assert "сверить ожидания по роли" in prompt
    assert "ChatDesk AI" in prompt
    assert "RouteMate" in prompt
    assert "пользовательский опыт" in prompt
    assert "мой опыт будет полезен быстрее всего" in prompt
    assert "Ваш продукт интересен мне" not in prompt
    assert "Мне откликается направление компании" not in prompt
    assert "С вашим продуктом я знаком как пользователь" not in prompt
    assert "Будет интересно пообщаться" not in prompt
    assert "На разговоре предложу" not in prompt
    assert "не только" not in prompt
    assert "не только писать код, но и" not in prompt
    assert "важны не только" not in prompt
    assert "план доработок" not in prompt
    assert "как бы я взял его в работу" not in prompt
    assert "Backend Developer" in prompt
    assert "Example LLC" in prompt
    assert "Build APIs and async workers." in prompt
    assert "<p>" not in prompt
    assert "FastAPI, PostgreSQL" in prompt
    assert "3-6 years" not in prompt
    assert "Full time" not in prompt
    assert "Remote" not in prompt


async def create_user_with_profile(fixture: CoverLetterFixture) -> User:
    user = await fixture.user_repo.create(
        User(
            telegram_id=1001,
            plan=Plan.FREE,
            credits=1,
        ),
    )
    await fixture.profile_repo.create(
        ResumeProfile(
            user_id=required_id(user),
            resume_text="Python developer with FastAPI and PostgreSQL experience. " * 3,
        ),
    )
    return user


def required_id(entity: object) -> int:
    entity_id = getattr(entity, "id", None)
    if not isinstance(entity_id, int):
        raise ValueError("entity id is not assigned")

    return entity_id


def only[T](items: list[T]) -> T:
    assert len(items) == 1
    return items[0]
