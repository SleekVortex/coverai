import hashlib
import hmac
import secrets

from coverai.services.config import SERVICE_CONFIG

_AUTH_CONFIG = SERVICE_CONFIG.auth
PASSWORD_HASH_ITERATIONS = _AUTH_CONFIG.password_hash_iterations


def hash_password(password: str) -> str:
    """Хэширует пароль."""
    salt = secrets.token_hex(_AUTH_CONFIG.password_salt_bytes)
    digest = hashlib.pbkdf2_hmac(
        _AUTH_CONFIG.password_digest_name,
        password.encode("utf-8"),
        salt.encode("ascii"),
        _AUTH_CONFIG.password_hash_iterations,
    ).hex()
    return (
        f"{_AUTH_CONFIG.password_algorithm}$"
        f"{_AUTH_CONFIG.password_hash_iterations}${salt}${digest}"
    )


def verify_password(password: str, stored_hash: str | None) -> bool:
    """Проверяет пароль."""
    if not stored_hash:
        return False

    try:
        algorithm, iterations_text, salt, expected = stored_hash.split("$", 3)
        iterations = int(iterations_text)
    except ValueError:
        return False

    if algorithm != _AUTH_CONFIG.password_algorithm:
        return False

    digest = hashlib.pbkdf2_hmac(
        _AUTH_CONFIG.password_digest_name,
        password.encode("utf-8"),
        salt.encode("ascii"),
        iterations,
    ).hex()
    return hmac.compare_digest(digest, expected)
