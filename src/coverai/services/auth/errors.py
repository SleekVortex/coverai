class AuthError(Exception):
    pass


class InvalidCredentialsError(AuthError):
    pass


class ForbiddenError(AuthError):
    pass
