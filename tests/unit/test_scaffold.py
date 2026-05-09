from coverai.configs import Settings
from coverai.domain.enums import Plan, Tone
from coverai.workers.settings import WorkerSettings
from coverai.workers.tasks import generate_cover_letter


def test_settings_defaults() -> None:
    settings = Settings(_env_file=None)

    assert settings.app.timezone == "Europe/Moscow"
    assert settings.llm.base_url == "https://openrouter.ai/api/v1"
    assert settings.llm.model == "deepseek/deepseek-chat-v3.2"
    assert settings.llm.proxy_url == ""
    assert settings.billing.standard_subscription_price_rub == 399
    assert settings.billing.pro_subscription_price_rub == 999
    assert settings.telegram.proxy_url == ""
    assert settings.hh.access_token == ""
    assert settings.hh.user_agent == "coverai/0.1.0"
    assert settings.hh.proxy_url == ""
    assert settings.hh.html_fallback_enabled is True


def test_settings_accept_generic_llm_env_names() -> None:
    settings = Settings(
        LLM_API_KEY="generic-key",
        LLM_BASE_URL="https://llm.example.test/v1",
        LLM_MODEL="provider/model",
        LLM_PROXY_URL="http://proxy.example.test:8080",
    )

    assert settings.llm.api_key == "generic-key"
    assert settings.llm.base_url == "https://llm.example.test/v1"
    assert settings.llm.model == "provider/model"
    assert settings.llm.proxy_url == "http://proxy.example.test:8080"


def test_settings_accept_legacy_openrouter_env_names() -> None:
    settings = Settings(
        OPENROUTER_API_KEY="legacy-key",
        OPENROUTER_BASE_URL="https://openrouter.ai/api/v1",
        PRIMARY_LLM_MODEL="deepseek/deepseek-chat-v3.2",
    )

    assert settings.llm.api_key == "legacy-key"
    assert settings.llm.base_url == "https://openrouter.ai/api/v1"
    assert settings.llm.model == "deepseek/deepseek-chat-v3.2"


def test_domain_enums_match_mvp_scope() -> None:
    assert Plan.FREE == "free"
    assert Plan.STANDARD == "standard"
    assert Plan.PRO == "pro"
    assert Tone.FORMAL == "formal"


def test_worker_settings_is_importable() -> None:
    assert WorkerSettings.functions == [generate_cover_letter]
