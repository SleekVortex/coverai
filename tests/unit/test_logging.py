from coverai.infra.logging import redact_log_secrets


def test_redacts_telegram_bot_token_from_logs() -> None:
    message = (
        "HTTP Request: POST "
        "https://api.telegram.org/bot123:secret-token/sendMessage "
        '"HTTP/1.1 200 OK"'
    )

    assert redact_log_secrets(message) == (
        "HTTP Request: POST "
        "https://api.telegram.org/bot<redacted>/sendMessage "
        '"HTTP/1.1 200 OK"'
    )
