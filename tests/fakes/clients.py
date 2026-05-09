from dataclasses import dataclass

from coverai.domain.hh import HHClientError, HHEmployerPayload, HHVacancyPayload
from coverai.domain.llm import LLMClientError, LLMCompletion


class FakeLLMClient:
    def __init__(
        self,
        text: str = "Здравствуйте! Хочу откликнуться на вакансию.",
        error: Exception | None = None,
        model: str = "test-model",
    ) -> None:
        self.text = text
        self.error = error
        self.model = model
        self.prompts: list[str] = []

    async def generate_cover_letter(self, prompt: str) -> LLMCompletion:
        self.prompts.append(prompt)
        if self.error is not None:
            raise self.error
        return LLMCompletion(text=self.text, model=self.model, generation_ms=123)


class FakeHHClient:
    def __init__(
        self,
        vacancy_error: Exception | None = None,
        employer_error: Exception | None = None,
        archived: bool = False,
        type_id: str = "open",
    ) -> None:
        self.vacancy_error = vacancy_error
        self.employer_error = employer_error
        self.archived = archived
        self.type_id = type_id
        self.vacancy_calls: list[int] = []
        self.employer_calls: list[int] = []

    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        self.vacancy_calls.append(hh_id)
        if self.vacancy_error is not None:
            raise self.vacancy_error
        return HHVacancyPayload(
            hh_id=hh_id,
            title="Python Developer",
            employer_hh_id=456,
            employer_name="Example LLC",
            url=f"https://hh.ru/vacancy/{hh_id}",
            archived=self.archived,
            type_id=self.type_id,
            raw_payload={"id": str(hh_id), "name": "Python Developer"},
        )

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        self.employer_calls.append(hh_id)
        if self.employer_error is not None:
            raise self.employer_error
        return HHEmployerPayload(
            hh_id=hh_id,
            name="Example LLC",
            url=f"https://hh.ru/employer/{hh_id}",
            raw_payload={"id": str(hh_id), "name": "Example LLC"},
        )


@dataclass(slots=True)
class FakeTelegramSender:
    messages: list[tuple[int, str]]

    async def send_message(self, telegram_id: int, text: str) -> None:
        self.messages.append((telegram_id, text))


def llm_timeout() -> LLMClientError:
    return LLMClientError("llm timeout")


def hh_unavailable() -> HHClientError:
    return HHClientError("hh.ru unavailable")
