from typing import Protocol


class TokenSettings(Protocol):
    jwt_secret: str
    jwt_algorithm: str
    access_token_expire_minutes: int

