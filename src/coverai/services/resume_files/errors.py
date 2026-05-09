from coverai.services.base_error import CoverAIServiceError


class UnsupportedResumeFileError(CoverAIServiceError):
    pass


class ResumeTextNotExtractedError(CoverAIServiceError):
    pass
