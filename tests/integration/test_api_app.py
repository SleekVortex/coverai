from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import StaticPool

from coverai.api.app import create_app
from coverai.configs import Settings
from coverai.infra.db.base import Base
from coverai.infra.db.session import create_session_factory


class FakeArqPool:
    def __init__(self) -> None:
        self.jobs: list[tuple[str, tuple[object, ...]]] = []

    async def enqueue_job(self, name: str, *args: object) -> None:
        self.jobs.append((name, args))


@pytest.fixture
def api_client() -> Iterator[tuple[TestClient, FakeArqPool]]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
    )

    async def create_schema() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    import asyncio

    asyncio.run(create_schema())
    arq_pool = FakeArqPool()
    app = create_app(
        settings=Settings(
            _env_file=None,
            JWT_SECRET="test-secret-for-api-tests-32-bytes",
            ADMIN_EMAIL="admin@example.test",
            ADMIN_PASSWORD="admin-password",
        ),
        session_factory=create_session_factory(engine),
        arq_pool=arq_pool,
    )
    with TestClient(app) as client:
        yield client, arq_pool

    asyncio.run(engine.dispose())


def test_register_login_and_openapi(api_client: tuple[TestClient, FakeArqPool]) -> None:
    client, _arq_pool = api_client

    token = register_user(client)
    me = client.get("/users/me", headers=auth(token))

    assert me.status_code == 200
    assert me.json()["email"] == "user@example.test"
    assert client.get("/openapi.json").json()["paths"]["/generations"]


def test_profile_validation_errors(api_client: tuple[TestClient, FakeArqPool]) -> None:
    client, _arq_pool = api_client
    token = register_user(client)

    too_short = client.put(
        "/profile",
        headers=auth(token),
        json={"resume_text": "too short"},
    )

    assert too_short.status_code == 422
    assert too_short.json()["detail"] == "Resume text is too short"


def test_promo_payment_and_generation_queue(
    api_client: tuple[TestClient, FakeArqPool],
) -> None:
    client, arq_pool = api_client
    user_token = register_user(client)
    admin_token = login(client, "admin@example.test", "admin-password")

    promo = client.post(
        "/admin/promocodes",
        headers=auth(admin_token),
        json={
            "code": "WELCOME100",
            "type": "fixed_credits",
            "value": 100,
            "valid_until": "2099-01-01T00:00:00Z",
            "max_activations": 1,
        },
    )
    assert promo.status_code == 200

    redeemed = client.post(
        "/promocodes/redeem",
        headers=auth(user_token),
        json={"code": "welcome100"},
    )
    assert redeemed.status_code == 200
    assert (
        client.get("/billing/balance", headers=auth(user_token)).json()["credits"]
        == 101
    )

    duplicate = client.post(
        "/promocodes/redeem",
        headers=auth(user_token),
        json={"code": "WELCOME100"},
    )
    assert duplicate.status_code == 409

    profile = client.put(
        "/profile",
        headers=auth(user_token),
        json={"resume_text": "Python backend developer " * 8},
    )
    assert profile.status_code == 200

    generation = client.post(
        "/generations",
        headers=auth(user_token),
        json={"vacancy_url": "https://hh.ru/vacancy/123", "tone": "formal"},
    )
    assert generation.status_code == 202
    generation_payload = generation.json()
    assert generation_payload["generation_request_id"] > 0
    assert generation_payload["status"] == "pending"
    assert arq_pool.jobs == [
            (
                "generate_cover_letter",
                (
                    2,
                    "https://hh.ru/vacancy/123",
                    "formal",
                    False,
                    True,
                    1,
                    generation_payload["generation_request_id"],
                ),
            ),
        ]
    status_response = client.get(
        f"/generations/{generation_payload['generation_request_id']}",
        headers=auth(user_token),
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "pending"


def test_generation_queue_rejects_invalid_requests(
    api_client: tuple[TestClient, FakeArqPool],
) -> None:
    client, arq_pool = api_client
    user_token = register_user(client)
    profile = client.put(
        "/profile",
        headers=auth(user_token),
        json={"resume_text": "Python backend developer " * 8},
    )
    assert profile.status_code == 200

    invalid_url = client.post(
        "/generations",
        headers=auth(user_token),
        json={"vacancy_url": "https://example.com/vacancy/123", "tone": "formal"},
    )
    assert invalid_url.status_code == 422

    forbidden_tone = client.post(
        "/generations",
        headers=auth(user_token),
        json={"vacancy_url": "https://hh.ru/vacancy/123", "tone": "confident"},
    )
    assert forbidden_tone.status_code == 403
    assert arq_pool.jobs == []

    first_generation = client.post(
        "/generations",
        headers=auth(user_token),
        json={"vacancy_url": "https://hh.ru/vacancy/123", "tone": "formal"},
    )
    assert first_generation.status_code == 202
    quota_exceeded = client.post(
        "/generations",
        headers=auth(user_token),
        json={"vacancy_url": "https://hh.ru/vacancy/456", "tone": "formal"},
    )
    assert quota_exceeded.status_code == 429
    assert len(arq_pool.jobs) == 1


def test_mock_payment_with_discount(api_client: tuple[TestClient, FakeArqPool]) -> None:
    client, _arq_pool = api_client
    user_token = register_user(client)
    admin_token = login(client, "admin@example.test", "admin-password")

    client.post(
        "/admin/promocodes",
        headers=auth(admin_token),
        json={
            "code": "SAVE10",
            "type": "top_up_discount",
            "value": 10,
            "valid_until": "2099-01-01T00:00:00Z",
            "max_activations": 10,
        },
    )
    assert (
        client.post(
            "/promocodes/redeem",
            headers=auth(user_token),
            json={"code": "SAVE10"},
        ).status_code
        == 200
    )

    payment = client.post(
        "/payments",
        headers=auth(user_token),
        json={"credits_amount": 100},
    )
    assert payment.status_code == 200
    payment_payload = payment.json()
    assert payment_payload["discount_percent"] == 10
    assert payment_payload["amount_rub"] == 90

    confirmed = client.post(
        f"/webhooks/mock-payment/{payment_payload['external_id']}",
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "succeeded"
    assert (
        client.get("/billing/balance", headers=auth(user_token)).json()["credits"]
        == 101
    )


def register_user(client: TestClient) -> str:
    response = client.post(
        "/auth/register",
        json={"email": "user@example.test", "password": "secret12"},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def login(client: TestClient, email: str, password: str) -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return str(response.json()["access_token"])


def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}
