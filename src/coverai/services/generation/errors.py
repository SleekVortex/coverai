from coverai.services.base_error import CoverAIServiceError


class ForbiddenToneError(CoverAIServiceError):
    pass


class GenerationRequestNotFoundError(CoverAIServiceError):
    pass


class EmptyLLMResponseError(CoverAIServiceError):
    pass
