# CoverAI - архитектура

## Назначение

CoverAI генерирует сопроводительные письма для вакансий hh.ru на основе
сохраненного профиля резюме. У системы два канала доступа поверх общего
сервисного слоя:

- **Telegram-бот** - основной потребительский канал. Пользователь может начать с
  `/start`, отправить резюме, отправить ссылку на вакансию hh.ru и получить
  готовое письмо без email/password логина.
- **REST API** - административный и интеграционный канал с JWT-авторизацией. Он
  открывает операции с пользователями, профилями, генерациями, биллингом,
  аналитикой и admin endpoints для поддержки сервиса и будущих внешних клиентов.

Бизнес-правила одинаковы во всех каналах: кредиты, лимиты тарифов, подписки,
доступ к истории, доступные тоны, ledger биллинга и статусы генерации. Telegram-
и API-аккаунты независимы в MVP; объединение аккаунтов вне scope.

## Стек

| Компонент | Технология |
| --- | --- |
| REST API | FastAPI, Uvicorn, JWT, Swagger/OpenAPI |
| Bot | aiogram 3 |
| Worker | arq async worker |
| DB | PostgreSQL 16 |
| ORM | SQLAlchemy 2.0 |
| Миграции | Alembic |
| Очередь | Redis 7 |
| Метрики | Prometheus client, Prometheus |
| Дашборды | Grafana |
| Контейнеры | Docker Compose |

## Внешние API и провайдеры

| Назначение | Провайдер |
| --- | --- |
| Telegram updates/messages | Telegram Bot API |
| Вакансии и работодатели | hh.ru API, optional HTML fallback |
| LLM | `LLM_MODEL`, по умолчанию `deepseek/deepseek-chat-v3.2` |
| LLM endpoint | OpenAI-compatible HTTP API, OpenRouter по умолчанию |
| Платежи | Payment intent abstraction; local/mock provider в MVP/dev |

- Оценочная стоимость LLM: около `$0.001` за письмо.
- Ответы вакансий и работодателей кэшируются в PostgreSQL через `cached_at` с
  TTL 1 час. Redis используется для очереди arq, не как источник истины для
  кэша вакансий.
- hh.ru API - основной источник вакансий. HTML fallback разрешен как
  технический источник при fallback-eligible ошибках API или rate limits.
- LLM-запросы идут в один настроенный OpenAI-compatible endpoint. Если LLM
  вернул ошибку, timeout, невалидный JSON или пустой текст, generation request
  получает статус `failed`.
- `TELEGRAM_PROXY_URL`, `HH_PROXY_URL` и `LLM_PROXY_URL` задают прокси для
  исходящих запросов к внешним API.

## Потоки выполнения

### Генерация через Telegram

Целевая latency после старта worker job: около 3-7 секунд.

1. Пользователь отправляет текст резюме или файл в бот.
2. Бот сохраняет одну запись `resume_profiles` для Telegram-пользователя.
3. Пользователь отправляет ссылку `https://hh.ru/vacancy/{id}`.
4. Бот проверяет профиль, баланс кредитов, лимит тарифа и доступ к tone.
5. Бот атомарно резервирует `generation_requests` со статусом `pending`,
   сохраняет snapshot профиля и tone, создает placeholder vacancy при
   необходимости и ставит `generate_cover_letter` в Redis/arq.
6. Worker загружает generation request и актуальные данные вакансии через
   hh.ru API или HTML fallback.
7. Worker строит prompt из snapshot профиля, загруженной вакансии и tone из
   generation request.
8. Worker вызывает настроенный LLM provider.
9. Worker сохраняет `cover_letters`, переводит `generation_requests` в
   `succeeded` и записывает `credit_transactions` со списанием в одной DB
   transaction.
10. Бот отправляет пользователю готовое письмо.

### Генерация через REST API

1. Клиент регистрируется или логинится через `/auth/*` и получает JWT.
2. Клиент создает или обновляет `/profile`.
3. Клиент вызывает `POST /generations` с `vacancy_url` и опциональным `tone`.
4. API проверяет ownership, профиль, кредиты, лимиты тарифа и доступ к tone.
5. API атомарно резервирует `generation_requests` со статусом `pending` и
   фиксирует snapshot профиля и tone.
6. API возвращает `202 Accepted` с идентификатором генерации и ставит job в
   очередь.
7. Клиент опрашивает `GET /generations/{id}` или читает `/generations/history`.

Free-пользователи могут использовать только `formal` tone. Standard и Pro могут
использовать `formal`, `confident` и `concise`.

## Инфраструктура

```text
Telegram Bot API -> bot (aiogram) -----> PostgreSQL
                         |              (users, profiles, billing, requests)
                         v
                    Redis / arq
                         ^
                         |
REST clients/admins -> api (FastAPI) --> PostgreSQL
                         |              (users, profiles, billing, requests)
                         v
                    Redis / arq
                         |
                         v
                    worker (arq) ------> PostgreSQL
                     /    |              (snapshots, letters, billing)
                    /     |
             hh.ru API  LLM

Prometheus --scrapes /metrics--> api
Prometheus --scrapes /metrics--> bot
Prometheus --scrapes /metrics--> worker
Grafana -----------------------> Prometheus
```

- 7 Docker services: `api`, `bot`, `worker`, `postgres`, `redis`,
  `prometheus`, `grafana`.
- `api`, `bot` и `worker` используют один application image из
  `./docker/Dockerfile`.
- `api` запускает `alembic upgrade head` перед стартом Uvicorn. Отдельного
  compose-сервиса migrations сейчас нет.
- `worker` отвечает за async generation jobs.
- `api` и `bot` напрямую читают/пишут PostgreSQL для пользователей, профилей,
  биллинга, quota checks и резервирования `pending` generation.
- Вся система должна запускаться через Docker Compose.
- Команда локального запуска: `docker compose up --build`.
- Fresh clone с валидным `.env` не должен требовать установки Python,
  PostgreSQL, Redis, Prometheus или Grafana на host machine.

## Слои

Импорты должны идти только вниз.

| Слой | Ответственность |
| --- | --- |
| entrypoints | `api/` FastAPI routes; `bot/` handlers; `workers/` arq tasks |
| services | Profile, generation, vacancy, billing, quota, history, analytics use cases |
| repos / clients | SQLAlchemy repositories, `HHClient`, `LLMClient`, Telegram sender |
| infra | DB engine/session, Redis pool, config, logging, metrics, security helpers |
| domain | Entities, enums, ports/protocols; stdlib-only business primitives |

Entrypoints адаптируют транспортные детали в вызовы сервисов. Бизнес-правила
живут в services, а не в FastAPI routes, aiogram handlers или arq task glue.

## Инфраструктурные сервисы

### docker compose

| Поле | Значение |
| --- | --- |
| Файл | `docker-compose.yml` |
| Запуск | `docker compose up --build` |
| Сервисы | `api`, `bot`, `worker`, `postgres`, `redis`, `prometheus`, `grafana` |
| App image | Собирается из `./docker/Dockerfile` и используется `api`, `bot`, `worker` |
| Env | Загружается из `.env`, если файл есть |
| Volumes | `pg_data`, `prometheus_data`, `grafana_data` |
| Healthchecks | API `/health`; bot `/metrics`; worker `/metrics`; postgres; redis |
| Acceptance | Все сервисы стартуют из fresh clone при наличии Docker и валидного `.env` |

### api

| Поле | Значение |
| --- | --- |
| Образ | `./docker/Dockerfile` |
| Команда | `alembic upgrade head && uvicorn coverai.api.app:app --host 0.0.0.0 --port 8000` |
| Фреймворк | FastAPI |
| Auth | JWT bearer tokens, роли `user` и `admin` |
| Документация | Swagger UI на `/docs`, OpenAPI на `/openapi.json` |
| Health | `/health` |
| Metrics | `/metrics` |
| Порт | `8000` |
| Зависит от | postgres, redis |

API создает первого администратора из `ADMIN_EMAIL` и `ADMIN_PASSWORD` при
старте, если admin с таким email еще не существует. Пароль существующего admin
не перезаписывается из переменных окружения.

### bot

| Поле | Значение |
| --- | --- |
| Образ | `./docker/Dockerfile` |
| Команда | `python -m coverai.main` |
| Фреймворк | aiogram 3 |
| Healthcheck | `/metrics` |
| Metrics | `/metrics` |
| Порт | `8002` |
| Зависит от | postgres, redis |

`coverai.main` - текущий bot runner entrypoint.

### worker

| Поле | Значение |
| --- | --- |
| Образ | `./docker/Dockerfile` |
| Команда | `arq coverai.workers.settings.WorkerSettings` |
| Режим | arq async task queue |
| Задачи | `generate_cover_letter` |
| Healthcheck | `/metrics` |
| Metrics | `/metrics` |
| Порт | `8001` |
| Зависит от | postgres, redis |

У `api` отдельный health endpoint `/health`. `bot` и `worker` поднимают
Prometheus metrics server; compose healthcheck для них проверяет `/metrics`.

### postgres

| Поле | Значение |
| --- | --- |
| Образ | `postgres:16-alpine` |
| DB | `coverai` по умолчанию |
| Volume | `pg_data:/var/lib/postgresql/data` |
| Миграции | Alembic |
| Core tables | `users`, `resume_profiles`, `generation_requests`, `cover_letters`, `vacancies`, `employers` |
| Billing tables | `subscriptions`, `credit_transactions`, `payment_intents`, `subscription_payment_intents`, `promo_codes`, `promo_redemptions` |

`generation_requests` хранит immutable snapshot fields, которые нужны async
worker: `snapshot_profile_text`, `snapshot_vacancy_text`, `snapshot_tone`.
Worker использует snapshot профиля и tone из request, а данные вакансии
обновляет через vacancy service перед генерацией.

### redis

| Поле | Значение |
| --- | --- |
| Образ | `redis:7-alpine` |
| Broker | arq task queue |
| Persistence | ephemeral |

Промежуточный выбор tone в Telegram хранится в in-memory `PendingToneStore` в
процессе bot, а не в Redis.

### prometheus

| Поле | Значение |
| --- | --- |
| Образ | `prom/prometheus` |
| Назначение | Сбор метрик |
| Scrape targets | `api:8000/metrics`, `bot:8002/metrics`, `worker:8001/metrics` |
| Порт | `9090` |
| Зависит от | api, bot, worker |

### grafana

| Поле | Значение |
| --- | --- |
| Образ | `grafana/grafana` |
| Назначение | Дашборды метрик |
| Источник данных | Prometheus |
| Порт | `3000` |
| Дашборды | Generation status, latency, queue size, quota usage, external API latency |
| Зависит от | prometheus |

## REST API

Пользовательские и интеграционные endpoints:

- `POST /auth/register`
- `POST /auth/login`
- `GET /users/me`
- `GET /profile`
- `PUT /profile`
- `POST /generations`
- `GET /generations/{id}`
- `GET /generations/history`
- `GET /billing/balance`
- `GET /billing/transactions`
- `POST /payments`
- `POST /webhooks/mock-payment/{external_id}`
- `POST /webhooks/mock-payment/{external_id}/fail`
- `POST /webhooks/mock-payment/{external_id}/cancel`
- `POST /payments/{payment_id}/refund`
- `POST /subscriptions`
- `GET /subscriptions/current`
- `POST /subscriptions/current/cancel`
- `POST /promocodes/redeem`
- `GET /analytics/usage`

Административные endpoints:

- `GET /admin/users`
- `GET /admin/users/{id}`
- `POST /admin/users/{id}/balance-adjustment`
- `POST /admin/users/{id}/subscription/expire`
- `POST /admin/promocodes`
- `GET /admin/analytics/overview`

Все `/admin/*` endpoints требуют JWT auth с `role = admin`.

## Биллинг и подписки

Кредиты и подписки - разные продукты:

- Кредиты оплачивают успешные LLM-генерации.
- Подписка открывает тарифные возможности: повышенные лимиты, выбор тона,
  доступ к истории.
- Кредиты списываются только после успешной генерации.
- Failed generation requests не списывают кредиты и не учитываются в лимитах
  тарифа.
- `generation_requests` со статусом `pending` или `succeeded` учитываются в
  лимитах тарифа; `failed` не учитывается.
- Изменения баланса фиксируются в `credit_transactions`.
- `payment_intents` описывает попытки пополнения кредитов и хранит
  `credits_amount`, `amount_rub`, `discount_percent`, `provider`, `external_id`
  и статус.
- `subscription_payment_intents` описывает попытки оплаты подписки и хранит
  `plan`, `amount_rub`, `provider`, `external_id` и статус.
- Возможные `credit_transactions.type`: `welcome_bonus`, `top_up`, `spend`,
  `promo`, `adjustment`, `refund`.
- Возможные `promo_codes.type`: `fixed_credits`, `top_up_discount`.
- `fixed_credits` увеличивает `users.credits` и создает ledger row с
  `type = promo`.
- `top_up_discount` применяется только к пополнениям кредитов, не к подпискам.

## Тарифы

| Тариф | Цена | Лимиты | Возможности |
| --- | ---: | --- | --- |
| Free | 0 RUB / month | 1 generation / calendar day | 1 resume profile, `formal` tone, no history, welcome credits |
| Standard | 399 RUB / 30 days | 300 generations / calendar month | 1 resume profile, 3 tones, rolling 30-day history |
| Pro | 999 RUB / 30 days | Unlimited generations | 1 resume profile, 3 tones, unlimited history |

Период лимита Standard - календарный месяц в timezone `Europe/Moscow`. История
Standard - отдельное скользящее окно доступа за последние 30 дней.

## Наблюдаемость

Prometheus собирает метрики с API, bot и worker. Grafana визуализирует:

- generation requests по статусам и тарифам;
- generation latency;
- latency hh.ru и LLM;
- quota usage и limits;
- arq queue size;
- error rate.

Бизнес-метрики вроде active subscriptions, revenue, credits spent и users by
plan доступны через API/admin analytics и как Prometheus metrics.
