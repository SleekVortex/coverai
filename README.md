# CoverAI

CoverAI - сервис для генерации сопроводительных писем под вакансии hh.ru.
Пользователь сохраняет резюме, отправляет ссылку на вакансию, а система
загружает данные вакансии, собирает prompt и асинхронно генерирует письмо через
OpenAI-compatible LLM endpoint.

В репозитории реализован MVP с двумя пользовательскими входами:

- FastAPI REST API с JWT-аутентификацией, Swagger UI и mock-биллингом.
- Telegram-бот на aiogram, использующий те же БД, очередь, тарифы и worker.

Отдельной ML-модели в репозитории нет: генерация выполняется внешним LLM API.
По умолчанию используется OpenRouter-compatible endpoint и модель
`deepseek/deepseek-chat-v3.2`.

## Архитектура

Основной сценарий:

```text
REST API / Telegram bot
        |
        | validates profile, credits, vacancy URL
        v
Redis + arq queue
        |
        v
Worker
        |
        | loads hh.ru vacancy, builds prompt, calls LLM
        v
PostgreSQL
        |
        | stores request status, cover letter, credits ledger
        v
API history / Telegram notification / Grafana metrics
```

Система разделена на прикладные слои:

- `src/coverai/api` - FastAPI-приложение, схемы запросов/ответов,
  JWT-auth, профиль, генерации, история, баланс, mock-платежи, промокоды и
  простая пользовательская аналитика. Роуты, схемы, зависимости и mappers
  разнесены по доменным пакетам.
- `src/coverai/bot` - Telegram UI: команды, меню, загрузка резюме, выбор тона,
  история, баланс и постановка генераций в очередь. Handler-и, клавиатуры,
  formatters, parsing и runtime-код разделены по ответственности.
- `src/coverai/workers` - ARQ worker, который выполняет тяжелую генерацию вне
  request/response цикла.
- `src/coverai/services` - бизнес-логика, разложенная по bounded contexts:
  `auth`, `billing`, `credits`, `generation`, `history`, `profile`,
  `resume_files`, `users`, `vacancy`, `prompts`, `metrics`.
- `src/coverai/domain` - доменные dataclass-entity, enum-значения и порты для
  клиентов, репозиториев и метрик. Domain слой не зависит от FastAPI,
  SQLAlchemy, aiogram, Redis или ARQ.
- `src/coverai/repos` - SQLAlchemy-репозитории поверх async sessions, с
  отдельными repo-классами и mappers.
- `src/coverai/clients` - внешние клиенты: hh.ru API/HTML fallback,
  OpenAI-compatible LLM API и Telegram sender.
- `src/coverai/infra` - logging, Prometheus metrics, database session factory
  и инфраструктурные adapters.
- `src/coverai/configs` - typed settings, читаемые из `.env`.
- `src/coverai/di` - сборка зависимостей через Dishka.

## Стек

- Python 3.12
- FastAPI, Uvicorn
- aiogram 3
- arq, Redis
- PostgreSQL 16, SQLAlchemy 2 async, asyncpg
- Alembic
- Pydantic 2, pydantic-settings
- httpx
- PyMuPDF и python-docx для извлечения текста из резюме
- Prometheus client, Prometheus, Grafana
- Dishka для dependency injection
- uv для dependency management
- pytest, pytest-asyncio, pytest-cov, Ruff, mypy
- Docker Compose

## Данные

Основные таблицы:

- `users` - email/JWT пользователи, Telegram пользователи, роль, тариф,
  баланс кредитов и скидка на следующее пополнение.
- `resume_profiles` - один профиль резюме на пользователя.
- `employers` и `vacancies` - кэш данных hh.ru с `cached_at`.
- `generation_requests` - статус асинхронной генерации:
  `pending`, `succeeded`, `failed`.
- `cover_letters` - готовые письма, prompt context, модель и latency.
- `subscriptions` - активные подписки и срок действия тарифов.
- `payment_intents` - mock-платежи.
- `promo_codes` и `promo_redemptions` - промокоды и факты активации.
- `credit_transactions` - ledger всех изменений баланса кредитов.

Миграции лежат в `alembic/versions`.

## Биллинг и лимиты

В MVP используется внутренняя кредитная модель без реального платежного
провайдера.

- API и Telegram проверяют наличие профиля и достаточного баланса перед
  постановкой задачи.
- Кредиты списываются только worker-ом после успешного ответа LLM и сохранения
  письма.
- Ошибки hh.ru или LLM не списывают кредиты.
- Mock-платеж создается через `POST /payments` и подтверждается через
  `POST /webhooks/mock-payment/{external_id}`.
- Промокоды поддерживают фиксированное начисление кредитов или скидку на
  следующее пополнение.

Тарифные лимиты реализованы в `QuotaService`:

| Plan | Limit |
| --- | --- |
| `free` | 1 генерация в день |
| `standard` | 300 генераций в месяц |
| `pro` | безлимит |

День и месяц считаются в timezone `Europe/Moscow`. Для защиты от параллельных
запросов в лимит входят `pending` и `succeeded` генерации текущего периода.

Финансовая модель описана в [`docs/business-plan.md`](docs/business-plan.md).

## REST API

После запуска Swagger UI доступен на `http://localhost:8000/docs`.

Основной API flow:

1. Регистрация: `POST /auth/register`.
2. Логин: `POST /auth/login`.
3. Профиль резюме: `PUT /profile`, `GET /profile`.
4. Пополнение или промокод:
   - `POST /promocodes/redeem`
   - `POST /payments`
   - `POST /webhooks/mock-payment/{external_id}`
5. Постановка генерации: `POST /generations`.
6. История, баланс и аналитика:
   - `GET /generations/history`
   - `GET /billing/balance`
   - `GET /billing/transactions`
   - `GET /analytics/usage`

Admin endpoint:

- `POST /admin/promocodes` - создание промокодов пользователем с ролью `admin`.

## Telegram Bot

Бот запускается отдельным compose-сервисом `bot` и использует тот же Postgres,
Redis и worker, что и API.

Поддерживаемые команды:

- `/start`
- `/profile`
- `/plan` и `/balance`
- `/redeem`
- `/topup`
- `/subscribe`
- `/history`
- `/help`

Резюме можно отправить текстом или файлом. Поддерживаются `.txt`, `.md`,
`.docx`, `.pdf` с текстовым слоем. OCR не реализован.

## Инфраструктура

`docker-compose.yml` поднимает:

- `api` - FastAPI на `http://localhost:8000`.
- `bot` - Telegram bot polling и metrics endpoint.
- `worker` - ARQ worker и metrics endpoint.
- `postgres` - основная БД.
- `redis` - broker очереди ARQ.
- `prometheus` - сбор метрик на `http://localhost:9090`.
- `grafana` - дашборды на `http://localhost:3000`.

API и worker перед стартом выполняют `alembic upgrade head`.

## Конфигурация

Настройки читаются из `.env`; пример лежит в `.env.example`.

Ключевые переменные:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `HH_ACCESS_TOKEN`
- `HH_PROXY_URL`
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_PROXY_URL`
- `PREDICTION_COST_CREDITS`
- `CREDIT_PRICE_RUB`
- `STANDARD_SUBSCRIPTION_PRICE_RUB`
- `PRO_SUBSCRIPTION_PRICE_RUB`
- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

Поля `TELEGRAM_PROXY_URL`, `HH_PROXY_URL` и `LLM_PROXY_URL` задают прокси для
исходящих запросов к внешним API. В РФ прокси может быть нужен для обхода
блокировок Telegram, hh.ru или LLM-провайдера.

Если `TELEGRAM_BOT_TOKEN` пустой, bot-сервис остается запущенным, но не
стартует polling.

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

Полезные адреса:

- API: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Prometheus: `http://localhost:9090`
- Grafana: `http://localhost:3000`

## Локальные проверки

```bash
uv run ruff check .
uv run mypy src
uv run pytest
docker compose config
```

CI выполняет те же проверки в `.github/workflows/ci.yml`.

## Документация

- [`docs/business-plan.md`](docs/business-plan.md) - краткий бизнес-план,
  тарифы и финансовая модель.
- [`docs/cover-letter-bot-architecture.md`](docs/cover-letter-bot-architecture.md)
  - архитектурные заметки по боту.
- [`docs/bdd-specification.md`](docs/bdd-specification.md) - документированная
  BDD-спецификация; executable BDD tests в проекте больше не используются.
