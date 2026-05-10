from coverai.services.base_error import CoverAIServiceError


class InsufficientCreditsError(CoverAIServiceError):
    pass


class InvalidPaidPlanError(CoverAIServiceError):
    pass


class PaymentNotFoundError(CoverAIServiceError):
    pass


class PaymentNotRefundableError(CoverAIServiceError):
    pass


class PromoCodeAlreadyExistsError(CoverAIServiceError):
    pass


class PromoCodeAlreadyRedeemedError(CoverAIServiceError):
    pass


class PromoCodeInvalidError(CoverAIServiceError):
    pass


class PromoCodeInactiveError(PromoCodeInvalidError):
    pass


class PromoCodeExpiredError(PromoCodeInvalidError):
    pass


class PromoCodeActivationLimitReachedError(PromoCodeInvalidError):
    pass


class PromoCodeNotFoundError(CoverAIServiceError):
    pass


class QuotaExceededError(CoverAIServiceError):
    pass


class UserBalanceCannotBeNegativeError(CoverAIServiceError):
    pass
