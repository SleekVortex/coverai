from coverai.services.base_error import CoverAIServiceError


class UserNotFoundError(CoverAIServiceError):
    pass


class UserAlreadyExistsError(CoverAIServiceError):
    pass
