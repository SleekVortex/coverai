from coverai.services.base_error import CoverAIServiceError


class InsufficientCreditsError(CoverAIServiceError):
    pass


class InvalidPaidPlanError(CoverAIServiceError):
    pass


class QuotaExceededError(CoverAIServiceError):
    pass
