from coverai.services.base_error import CoverAIServiceError


class ProfileAlreadyExistsError(CoverAIServiceError):
    pass


class ProfileNotFoundError(CoverAIServiceError):
    pass


class InvalidProfileTitleError(CoverAIServiceError):
    pass


class ResumeTextTooShortError(CoverAIServiceError):
    pass
