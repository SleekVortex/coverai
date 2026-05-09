from coverai.services.base_error import CoverAIServiceError


class HistoryAccessDeniedError(CoverAIServiceError):
    pass


class CoverLetterNotFoundError(CoverAIServiceError):
    pass
