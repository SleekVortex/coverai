import re
from urllib.parse import urlparse

from coverai.services.config import SERVICE_CONFIG
from coverai.services.vacancy.errors import (
    InvalidVacancyUrlError,
    MultipleVacancyUrlsError,
)

URL_PATTERN = SERVICE_CONFIG.vacancy.hh_url_pattern


def parse_hh_vacancy_id(message_text: str) -> int:
    """Извлекает id вакансии hh.ru."""
    vacancy_ids: list[int] = []

    for raw_url in URL_PATTERN.findall(message_text):
        url = raw_url.rstrip(".,;:!?)]}")
        parsed = urlparse(url)
        host = parsed.hostname.lower() if parsed.hostname else ""
        if not is_hh_host(host):
            continue

        match = re.fullmatch(r"/vacancy/(\d+)/?", parsed.path)
        if match is None:
            continue

        vacancy_ids.append(int(match.group(1)))

    if len(vacancy_ids) > 1:
        raise MultipleVacancyUrlsError
    if not vacancy_ids:
        raise InvalidVacancyUrlError

    return vacancy_ids[0]


def is_hh_host(host: str) -> bool:
    """Проверяет host hh.ru."""
    root_host = SERVICE_CONFIG.vacancy.hh_root_host
    return host == root_host or host.endswith(f".{root_host}")
