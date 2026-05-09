from collections.abc import Awaitable, Callable

import httpx
import pytest

from coverai.clients.hh import HHApiVacancySource, HHHtmlVacancySource, HttpxHHClient
from coverai.domain.hh import HHClientError, VacancyNotFoundError


async def test_hh_client_fetches_vacancy_and_employer() -> None:
    client = HttpxHHClient(mock_client(successful_hh_response))

    vacancy = await client.get_vacancy(123)
    employer = await client.get_employer(456)

    assert vacancy.hh_id == 123
    assert vacancy.title == "Python Developer"
    assert vacancy.employer_hh_id == 456
    assert vacancy.type_id == "open"
    assert vacancy.archived is False
    assert employer.hh_id == 456
    assert employer.name == "Example Inc"


async def test_hh_client_maps_404_to_vacancy_not_found() -> None:
    client = HttpxHHClient(mock_client(not_found_response))

    with pytest.raises(VacancyNotFoundError):
        await client.get_vacancy(123)


async def test_hh_client_maps_5xx_to_client_error() -> None:
    client = HttpxHHClient(
        mock_client(server_error_response),
        html_fallback_enabled=False,
    )

    with pytest.raises(HHClientError):
        await client.get_vacancy(123)


async def test_hh_client_maps_network_error_to_client_error() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("network down", request=request)

    client = HttpxHHClient(mock_client(handler), html_fallback_enabled=False)

    with pytest.raises(HHClientError):
        await client.get_vacancy(123)


async def test_hh_client_does_not_fallback_on_404() -> None:
    html_calls: list[str] = []

    def html_handler(request: httpx.Request) -> httpx.Response:
        html_calls.append(request.url.path)
        return httpx.Response(status_code=200, text=data_qa_html())

    client = HttpxHHClient(
        api_source=HHApiVacancySource(mock_client(not_found_response)),
        html_source=HHHtmlVacancySource(mock_client(html_handler, "https://hh.ru")),
    )

    with pytest.raises(VacancyNotFoundError):
        await client.get_vacancy(123)

    assert html_calls == []


@pytest.mark.parametrize("status_code", [403, 429, 503])
async def test_hh_client_falls_back_to_html_for_retryable_statuses(
    status_code: int,
) -> None:
    api_calls: list[str] = []
    html_calls: list[str] = []

    def api_handler(request: httpx.Request) -> httpx.Response:
        api_calls.append(request.url.path)
        return httpx.Response(status_code=status_code, json={"errors": []})

    def html_handler(request: httpx.Request) -> httpx.Response:
        html_calls.append(request.url.path)
        return httpx.Response(status_code=200, text=data_qa_html())

    client = HttpxHHClient(
        api_source=HHApiVacancySource(mock_client(api_handler)),
        html_source=HHHtmlVacancySource(mock_client(html_handler, "https://hh.ru")),
    )

    vacancy = await client.get_vacancy(123)
    employer = await client.get_employer(456)

    assert vacancy.title == "HTML Python Developer"
    assert employer.name == "HTML Example Inc"
    assert api_calls == ["/vacancies/123", "/employers/456"]
    assert html_calls == ["/vacancy/123", "/vacancy/123"]


@pytest.mark.parametrize(
    "error_type",
    [httpx.ConnectError, httpx.ReadTimeout],
)
async def test_hh_client_falls_back_to_html_for_network_and_timeout(
    error_type: type[httpx.RequestError],
) -> None:
    def api_handler(request: httpx.Request) -> httpx.Response:
        raise error_type("network down", request=request)

    def html_handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=200, text=data_qa_html())

    client = HttpxHHClient(
        api_source=HHApiVacancySource(mock_client(api_handler)),
        html_source=HHHtmlVacancySource(mock_client(html_handler, "https://hh.ru")),
    )

    vacancy = await client.get_vacancy(123)

    assert vacancy.title == "HTML Python Developer"


async def test_html_source_parses_json_ld_vacancy() -> None:
    client = HHHtmlVacancySource(mock_client(json_ld_response, "https://hh.ru"))

    vacancy = await client.get_vacancy(123)
    employer = await client.get_employer(456)

    assert vacancy.hh_id == 123
    assert vacancy.title == "JSON-LD Python Developer"
    assert vacancy.employer_hh_id == 456
    assert vacancy.raw_payload["description"] == "Build async services."
    assert employer.name == "JSON-LD Example Inc"


async def test_html_source_parses_data_qa_vacancy() -> None:
    client = HHHtmlVacancySource(mock_client(data_qa_response, "https://hh.ru"))

    vacancy = await client.get_vacancy(123)
    employer = await client.get_employer(456)

    assert vacancy.hh_id == 123
    assert vacancy.title == "HTML Python Developer"
    assert vacancy.employer_hh_id == 456
    assert vacancy.raw_payload["description"] == "Build APIs and workers."
    assert employer.name == "HTML Example Inc"


def mock_client(
    handler: Callable[
        [httpx.Request],
        httpx.Response | Awaitable[httpx.Response],
    ],
    base_url: str = "https://api.hh.ru",
) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url=base_url,
    )


def successful_hh_response(request: httpx.Request) -> httpx.Response:
    if request.url.path == "/vacancies/123":
        return httpx.Response(
            status_code=200,
            json={
                "id": "123",
                "name": "Python Developer",
                "alternate_url": "https://hh.ru/vacancy/123",
                "archived": False,
                "type": {"id": "open", "name": "Open"},
                "employer": {
                    "id": "456",
                    "name": "Example Inc",
                    "alternate_url": "https://hh.ru/employer/456",
                },
            },
        )
    if request.url.path == "/employers/456":
        return httpx.Response(
            status_code=200,
            json={
                "id": "456",
                "name": "Example Inc",
                "alternate_url": "https://hh.ru/employer/456",
            },
        )

    return httpx.Response(status_code=404)


def not_found_response(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(status_code=404, json={"errors": [{"type": "not_found"}]})


def server_error_response(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(status_code=503, json={"errors": []})


def json_ld_response(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        status_code=200,
        text="""
            <html>
                <head>
                    <script type="application/ld+json">
                        {
                            "@context": "https://schema.org",
                            "@type": "JobPosting",
                            "title": "JSON-LD Python Developer",
                            "description": "Build async services.",
                            "hiringOrganization": {
                                "@type": "Organization",
                                "name": "JSON-LD Example Inc",
                                "sameAs": "https://hh.ru/employer/456"
                            }
                        }
                    </script>
                </head>
            </html>
        """,
    )


def data_qa_response(_request: httpx.Request) -> httpx.Response:
    return httpx.Response(status_code=200, text=data_qa_html())


def data_qa_html() -> str:
    return """
        <html>
            <body>
                <h1 data-qa="vacancy-title">HTML Python Developer</h1>
                <a data-qa="vacancy-company-name" href="/employer/456">
                    HTML Example Inc
                </a>
                <div data-qa="vacancy-description">
                    <p>Build APIs and workers.</p>
                </div>
            </body>
        </html>
    """
