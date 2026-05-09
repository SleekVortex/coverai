import pytest

from coverai.services.vacancy import parse_hh_vacancy_id
from coverai.services.vacancy.errors import (
    InvalidVacancyUrlError,
    MultipleVacancyUrlsError,
)


def test_parses_hh_vacancy_url() -> None:
    assert parse_hh_vacancy_id("https://hh.ru/vacancy/123456") == 123456


def test_parses_regional_hh_vacancy_url() -> None:
    assert parse_hh_vacancy_id("https://spb.hh.ru/vacancy/123456") == 123456


def test_parses_hh_vacancy_url_with_query_params() -> None:
    assert parse_hh_vacancy_id("https://hh.ru/vacancy/123456?from=vacancy_search") == (
        123456
    )


def test_rejects_multiple_hh_vacancy_urls() -> None:
    with pytest.raises(MultipleVacancyUrlsError):
        parse_hh_vacancy_id(
            "https://hh.ru/vacancy/123 https://hh.ru/vacancy/456",
        )


def test_rejects_non_hh_url() -> None:
    with pytest.raises(InvalidVacancyUrlError):
        parse_hh_vacancy_id("https://example.com/vacancy/123")


def test_rejects_hh_url_not_pointing_to_vacancy() -> None:
    with pytest.raises(InvalidVacancyUrlError):
        parse_hh_vacancy_id("https://hh.ru/employer/123")
