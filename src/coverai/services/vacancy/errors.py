from coverai.services.base_error import CoverAIServiceError


class InvalidVacancyUrlError(CoverAIServiceError):
    pass


class MultipleVacancyUrlsError(CoverAIServiceError):
    pass


class VacancyClosedError(CoverAIServiceError):
    pass
