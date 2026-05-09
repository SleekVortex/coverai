import json
import re
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from typing import Protocol, cast
from urllib.parse import urljoin

import httpx

from coverai.domain.hh import (
    HHClientError,
    HHEmployerPayload,
    HHVacancyPayload,
    VacancyNotFoundError,
)

HH_API_BASE_URL = "https://api.hh.ru"
HH_HTML_BASE_URL = "https://hh.ru"
HH_BASE_URL = HH_API_BASE_URL
HH_USER_AGENT = "coverai/0.1.0"

FALLBACK_STATUS_CODES = {403, 429}
DATA_QA_TITLE = "vacancy-title"
DATA_QA_COMPANY = "vacancy-company-name"
DATA_QA_DESCRIPTION = "vacancy-description"
DATA_QA_FIELDS = {DATA_QA_TITLE, DATA_QA_COMPANY, DATA_QA_DESCRIPTION}


class HHVacancySource(Protocol):
    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        """Возвращает вакансию."""
        ...

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        """Возвращает работодателя."""
        ...

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        ...


class _HHFallbackAllowedError(HHClientError):
    pass


class HttpxHHClient:
    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        *,
        access_token: str = "",
        user_agent: str = HH_USER_AGENT,
        proxy_url: str = "",
        html_fallback_enabled: bool = True,
        api_source: HHVacancySource | None = None,
        html_source: HHVacancySource | None = None,
    ) -> None:
        self._api_source = api_source or HHApiVacancySource(
            http_client=http_client,
            access_token=access_token,
            user_agent=user_agent,
            proxy_url=proxy_url,
        )
        self._html_source = html_source
        self._html_fallback_enabled = html_fallback_enabled
        self._html_user_agent = user_agent
        self._html_proxy_url = proxy_url
        self._vacancy_hh_id_by_employer_hh_id: dict[int, int] = {}

    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        """Возвращает вакансию."""
        try:
            payload = await self._api_source.get_vacancy(hh_id)
        except _HHFallbackAllowedError as error:
            payload = await self._get_vacancy_from_html(hh_id, error)

        self._vacancy_hh_id_by_employer_hh_id[payload.employer_hh_id] = payload.hh_id
        return payload

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        """Возвращает работодателя."""
        try:
            return await self._api_source.get_employer(hh_id)
        except _HHFallbackAllowedError as error:
            if not self._html_fallback_enabled:
                raise error

            vacancy_hh_id = self._vacancy_hh_id_by_employer_hh_id.get(hh_id)
            if vacancy_hh_id is not None:
                await self._html().get_vacancy(vacancy_hh_id)

            return await self._html().get_employer(hh_id)

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        await self._api_source.aclose()
        if self._html_source is not None:
            await self._html_source.aclose()

    async def _get_vacancy_from_html(
        self,
        hh_id: int,
        error: _HHFallbackAllowedError,
    ) -> HHVacancyPayload:
        if not self._html_fallback_enabled:
            raise error

        return await self._html().get_vacancy(hh_id)

    def _html(self) -> HHVacancySource:
        if self._html_source is None:
            self._html_source = HHHtmlVacancySource(
                user_agent=self._html_user_agent,
                proxy_url=self._html_proxy_url,
            )

        return self._html_source


class HHApiVacancySource:
    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        *,
        access_token: str = "",
        user_agent: str = HH_USER_AGENT,
        proxy_url: str = "",
    ) -> None:
        self._owns_client = http_client is None
        headers = {"User-Agent": user_agent}
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"

        self._client = http_client or httpx.AsyncClient(
            base_url=HH_API_BASE_URL,
            headers=headers,
            proxy=proxy_url or None,
            timeout=10.0,
        )

    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        """Возвращает вакансию."""
        payload = await self._get_json(f"/vacancies/{hh_id}")
        return vacancy_payload_from_json(payload)

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        """Возвращает работодателя."""
        payload = await self._get_json(f"/employers/{hh_id}")
        return employer_payload_from_json(payload)

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        if self._owns_client:
            await self._client.aclose()

    async def _get_json(self, path: str) -> dict[str, object]:
        try:
            response = await self._client.get(path)
        except httpx.TimeoutException as error:
            message = str(error) or "hh.ru request timed out"
            raise _HHFallbackAllowedError(message) from error
        except httpx.TransportError as error:
            raise _HHFallbackAllowedError(str(error)) from error

        if response.status_code == 404:
            raise VacancyNotFoundError
        if is_fallback_status(response.status_code):
            raise _HHFallbackAllowedError(
                f"hh.ru returned fallback-eligible status {response.status_code}",
            )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise HHClientError(str(error)) from error

        try:
            payload = response.json()
        except ValueError as error:
            raise HHClientError("hh.ru returned invalid JSON") from error

        if not isinstance(payload, dict):
            raise HHClientError("hh.ru returned non-object JSON")

        return cast("dict[str, object]", payload)


class HHHtmlVacancySource:
    def __init__(
        self,
        http_client: httpx.AsyncClient | None = None,
        *,
        user_agent: str = HH_USER_AGENT,
        proxy_url: str = "",
    ) -> None:
        self._owns_client = http_client is None
        self._client = http_client or httpx.AsyncClient(
            base_url=HH_HTML_BASE_URL,
            headers={"User-Agent": user_agent},
            proxy=proxy_url or None,
            timeout=10.0,
            follow_redirects=True,
        )
        self._employers_by_hh_id: dict[int, HHEmployerPayload] = {}

    async def get_vacancy(self, hh_id: int) -> HHVacancyPayload:
        """Возвращает вакансию."""
        response = await self._get(f"/vacancy/{hh_id}")
        parsed = parse_hh_vacancy_html(
            hh_id=hh_id,
            html=response.text,
            page_url=str(response.url),
        )
        vacancy, employer = parsed.to_payloads(hh_id=hh_id, page_url=str(response.url))
        self._employers_by_hh_id[employer.hh_id] = employer
        return vacancy

    async def get_employer(self, hh_id: int) -> HHEmployerPayload:
        """Возвращает работодателя."""
        employer = self._employers_by_hh_id.get(hh_id)
        if employer is None:
            raise HHClientError("hh.ru HTML fallback has no employer data")

        return employer

    async def aclose(self) -> None:
        """Закрывает ресурсы клиента."""
        if self._owns_client:
            await self._client.aclose()

    async def _get(self, path: str) -> httpx.Response:
        try:
            response = await self._client.get(
                path,
                headers={"Accept": "text/html,application/xhtml+xml"},
            )
        except httpx.HTTPError as error:
            raise HHClientError(str(error)) from error

        if response.status_code == 404:
            raise VacancyNotFoundError

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            raise HHClientError(str(error)) from error

        return response


@dataclass(frozen=True, slots=True)
class ParsedHHHtmlVacancy:
    title: str
    employer_hh_id: int
    employer_name: str
    employer_url: str | None
    description: str | None
    archived: bool = False

    def to_payloads(
        self,
        *,
        hh_id: int,
        page_url: str,
    ) -> tuple[HHVacancyPayload, HHEmployerPayload]:
        """Преобразует HTML-данные в payloads."""
        vacancy_url = page_url or f"{HH_HTML_BASE_URL}/vacancy/{hh_id}"
        employer_payload: dict[str, object] = {
            "id": str(self.employer_hh_id),
            "name": self.employer_name,
            "alternate_url": self.employer_url,
            "_source": "hh_html",
        }
        vacancy_payload: dict[str, object] = {
            "id": str(hh_id),
            "name": self.title,
            "alternate_url": vacancy_url,
            "archived": self.archived,
            "type": {"id": "closed" if self.archived else "open"},
            "employer": employer_payload,
            "description": self.description or "",
            "_source": "hh_html",
        }

        return (
            HHVacancyPayload(
                hh_id=hh_id,
                title=self.title,
                employer_hh_id=self.employer_hh_id,
                employer_name=self.employer_name,
                url=vacancy_url,
                archived=self.archived,
                type_id="closed" if self.archived else "open",
                raw_payload=vacancy_payload,
            ),
            HHEmployerPayload(
                hh_id=self.employer_hh_id,
                name=self.employer_name,
                url=self.employer_url,
                raw_payload=employer_payload,
            ),
        )


@dataclass(frozen=True, slots=True)
class _HtmlCandidate:
    title: str | None = None
    employer_name: str | None = None
    employer_url: str | None = None
    description: str | None = None
    archived: bool = False


@dataclass(slots=True)
class _HtmlCapture:
    key: str
    depth: int
    text_parts: list[str]
    href: str | None = None


class _HHVacancyHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.data_qa_texts: dict[str, list[str]] = {}
        self.data_qa_hrefs: dict[str, list[str]] = {}
        self.json_ld_scripts: list[str] = []
        self.meta_values: dict[str, str] = {}
        self._captures: list[_HtmlCapture] = []
        self._script_parts: list[str] | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        tag = tag.lower()
        attrs_by_name = {name.lower(): value or "" for name, value in attrs}

        if tag == "meta":
            self._capture_meta(attrs_by_name)
        if tag == "script" and self._is_json_ld(attrs_by_name):
            self._script_parts = []

        for capture in self._captures:
            capture.depth += 1
            if capture.href is None and attrs_by_name.get("href"):
                capture.href = attrs_by_name["href"]

        data_qa = attrs_by_name.get("data-qa")
        if data_qa in DATA_QA_FIELDS:
            self._captures.append(
                _HtmlCapture(
                    key=data_qa,
                    depth=1,
                    text_parts=[],
                    href=attrs_by_name.get("href") or None,
                ),
            )

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "script" and self._script_parts is not None:
            self.json_ld_scripts.append("".join(self._script_parts))
            self._script_parts = None

        completed: list[_HtmlCapture] = []
        for capture in self._captures:
            capture.depth -= 1
            if capture.depth == 0:
                completed.append(capture)

        for capture in completed:
            self._captures.remove(capture)
            text = normalize_text(" ".join(capture.text_parts))
            if text:
                self.data_qa_texts.setdefault(capture.key, []).append(text)
            if capture.href:
                self.data_qa_hrefs.setdefault(capture.key, []).append(capture.href)

    def handle_data(self, data: str) -> None:
        if self._script_parts is not None:
            self._script_parts.append(data)

        for capture in self._captures:
            capture.text_parts.append(data)

    def _capture_meta(self, attrs: dict[str, str]) -> None:
        key = attrs.get("property") or attrs.get("name")
        content = attrs.get("content")
        if key and content:
            self.meta_values[key.lower()] = content

    def _is_json_ld(self, attrs: dict[str, str]) -> bool:
        return attrs.get("type", "").lower() == "application/ld+json"


def vacancy_payload_from_json(payload: dict[str, object]) -> HHVacancyPayload:
    """Собирает payload вакансии из JSON."""
    employer = required_dict(payload, "employer")
    vacancy_type = optional_dict(payload, "type")

    return HHVacancyPayload(
        hh_id=required_int(payload, "id"),
        title=required_str(payload, "name"),
        employer_hh_id=required_int(employer, "id"),
        employer_name=required_str(employer, "name"),
        url=optional_str(payload, "alternate_url") or optional_str(payload, "url"),
        archived=payload.get("archived", False),
        type_id=optional_str(vacancy_type, "id") if vacancy_type else None,
        raw_payload=payload,
    )


def employer_payload_from_json(payload: dict[str, object]) -> HHEmployerPayload:
    """Собирает payload работодателя из JSON."""
    return HHEmployerPayload(
        hh_id=required_int(payload, "id"),
        name=required_str(payload, "name"),
        url=optional_str(payload, "alternate_url") or optional_str(payload, "site_url"),
        raw_payload=payload,
    )


def parse_hh_vacancy_html(
    *,
    hh_id: int,
    html: str,
    page_url: str,
) -> ParsedHHHtmlVacancy:
    """Парсит HTML страницы вакансии."""
    parser = _HHVacancyHTMLParser()
    parser.feed(html)

    data_qa_candidate = candidate_from_data_qa(parser, page_url)
    for candidate in candidates_from_json_ld(parser, page_url):
        parsed = complete_html_candidate(
            hh_id=hh_id,
            candidate=merge_candidates(candidate, data_qa_candidate),
            page_url=page_url,
        )
        if parsed is not None:
            return parsed

    parsed = complete_html_candidate(
        hh_id=hh_id,
        candidate=data_qa_candidate,
        page_url=page_url,
    )
    if parsed is not None:
        return parsed

    raise HHClientError("hh.ru HTML page did not contain vacancy data")


def candidate_from_data_qa(
    parser: _HHVacancyHTMLParser,
    page_url: str,
) -> _HtmlCandidate:
    """Извлекает кандидата из data-qa."""
    title = first_text(parser.data_qa_texts, DATA_QA_TITLE)
    employer_name = first_text(parser.data_qa_texts, DATA_QA_COMPANY)
    employer_url = first_text(parser.data_qa_hrefs, DATA_QA_COMPANY)
    description = first_text(parser.data_qa_texts, DATA_QA_DESCRIPTION)

    if title is None:
        title = normalize_title_from_meta(parser.meta_values.get("og:title"))

    archived_text = " ".join(
        text for texts in parser.data_qa_texts.values() for text in texts
    )
    return _HtmlCandidate(
        title=title,
        employer_name=employer_name,
        employer_url=absolute_url(employer_url, page_url),
        description=description,
        archived=is_archived_html_text(archived_text),
    )


def candidates_from_json_ld(
    parser: _HHVacancyHTMLParser,
    page_url: str,
) -> list[_HtmlCandidate]:
    """Извлекает кандидатов из JSON-LD."""
    candidates: list[_HtmlCandidate] = []
    for script in parser.json_ld_scripts:
        try:
            value = json.loads(script)
        except ValueError:
            continue

        for item in iter_json_dicts(value):
            if not has_json_ld_type(item, "JobPosting"):
                continue

            employer = first_json_dict(item.get("hiringOrganization"))
            employer_url = None
            employer_name = None
            if employer is not None:
                employer_name = json_str(employer, "name")
                employer_url = json_str(employer, "sameAs") or json_str(employer, "url")

            candidates.append(
                _HtmlCandidate(
                    title=json_str(item, "title") or json_str(item, "name"),
                    employer_name=employer_name,
                    employer_url=absolute_url(employer_url, page_url),
                    description=json_str(item, "description"),
                    archived=False,
                ),
            )

    return candidates


def complete_html_candidate(
    *,
    hh_id: int,
    candidate: _HtmlCandidate,
    page_url: str,
) -> ParsedHHHtmlVacancy | None:
    """Дополняет HTML-кандидата."""
    title = normalize_text(candidate.title or "")
    employer_name = normalize_text(candidate.employer_name or "")
    employer_hh_id = employer_id_from_url(candidate.employer_url)
    if not title or not employer_name or employer_hh_id is None:
        return None

    return ParsedHHHtmlVacancy(
        title=title,
        employer_hh_id=employer_hh_id,
        employer_name=employer_name,
        employer_url=absolute_url(candidate.employer_url, page_url),
        description=candidate.description,
        archived=candidate.archived or is_archived_html_text(candidate.title or ""),
    )


def merge_candidates(
    primary: _HtmlCandidate,
    fallback: _HtmlCandidate,
) -> _HtmlCandidate:
    """Объединяет данные кандидатов."""
    return _HtmlCandidate(
        title=primary.title or fallback.title,
        employer_name=primary.employer_name or fallback.employer_name,
        employer_url=primary.employer_url or fallback.employer_url,
        description=primary.description or fallback.description,
        archived=primary.archived or fallback.archived,
    )


def first_text(values: dict[str, list[str]], key: str) -> str | None:
    """Возвращает первый непустой текст."""
    for value in values.get(key, []):
        normalized = normalize_text(value)
        if normalized:
            return normalized

    return None


def normalize_text(value: str) -> str:
    """Нормализует текст."""
    return re.sub(r"\s+", " ", unescape(value)).strip()


def normalize_title_from_meta(value: str | None) -> str | None:
    """Нормализует title из meta."""
    if value is None:
        return None

    title = normalize_text(value)
    if " в компании " in title:
        return title.split(" в компании ", 1)[0].strip()

    return title


def is_archived_html_text(value: str) -> bool:
    """Проверяет архивный текст вакансии."""
    lowered = value.lower()
    return "вакансия в архиве" in lowered or "vacancy is archived" in lowered


def absolute_url(url: str | None, page_url: str) -> str | None:
    """Возвращает абсолютный URL."""
    if not url:
        return None

    return urljoin(page_url, url)


def employer_id_from_url(url: str | None) -> int | None:
    """Извлекает id работодателя из URL."""
    if not url:
        return None

    match = re.search(r"/employer/(\d+)", url)
    return int(match.group(1)) if match else None


def iter_json_dicts(value: object) -> list[dict[str, object]]:
    """Итерирует JSON-словари."""
    if isinstance(value, dict):
        result = [cast("dict[str, object]", value)]
        graph = value.get("@graph")
        if isinstance(graph, list):
            result.extend(iter_json_dicts(graph))
        return result
    if isinstance(value, list):
        items: list[dict[str, object]] = []
        for item in value:
            items.extend(iter_json_dicts(item))
        return items

    return []


def first_json_dict(value: object) -> dict[str, object] | None:
    """Возвращает первый JSON-словарь."""
    if isinstance(value, dict):
        return cast("dict[str, object]", value)
    if isinstance(value, list):
        for item in value:
            parsed = first_json_dict(item)
            if parsed is not None:
                return parsed

    return None


def has_json_ld_type(item: dict[str, object], expected_type: str) -> bool:
    """Проверяет тип JSON-LD."""
    value = item.get("@type")
    if isinstance(value, str):
        return value.lower() == expected_type.lower()
    if isinstance(value, list):
        return any(
            isinstance(type_item, str)
            and type_item.lower() == expected_type.lower()
            for type_item in value
        )

    return False


def json_str(item: dict[str, object], key: str) -> str | None:
    """Возвращает строковое JSON-поле."""
    value = item.get(key)
    if isinstance(value, str):
        normalized = normalize_text(value)
        return normalized or None

    return None


def is_fallback_status(status_code: int) -> bool:
    """Проверяет fallback HTTP-статус."""
    return status_code in FALLBACK_STATUS_CODES or status_code >= 500


def required_dict(payload: dict[str, object], field: str) -> dict[str, object]:
    """Возвращает обязательный словарь."""
    value = payload.get(field)
    if not isinstance(value, dict):
        raise HHClientError(f"hh.ru response misses object field {field}")

    return cast("dict[str, object]", value)


def optional_dict(payload: dict[str, object], field: str) -> dict[str, object] | None:
    """Возвращает необязательный словарь."""
    value = payload.get(field)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise HHClientError(f"hh.ru response has invalid object field {field}")

    return cast("dict[str, object]", value)


def required_int(payload: dict[str, object], field: str) -> int:
    """Возвращает обязательное число."""
    value = payload.get(field)
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.isdecimal():
        return int(value)

    raise HHClientError(f"hh.ru response misses integer field {field}")


def required_str(payload: dict[str, object], field: str) -> str:
    """Возвращает обязательную строку."""
    value = payload.get(field)
    if isinstance(value, str) and value:
        return value

    raise HHClientError(f"hh.ru response misses string field {field}")


def optional_str(payload: dict[str, object], field: str) -> str | None:
    """Возвращает необязательную строку."""
    value = payload.get(field)
    return value if isinstance(value, str) and value else None
