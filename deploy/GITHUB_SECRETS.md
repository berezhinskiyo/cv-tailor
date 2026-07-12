# Секреты и переменные GitHub — cv-tailor

Все секреты окружений живут в GitHub (Settings → Secrets and variables → Actions).
Деплой сам пишет `.env` на сервер из секрета `DOTENV` соответствующего Environment.
Вручную на сервере `.env` держать НЕ нужно.

## 1. Repository secrets
| Имя | Значение |
|-----|----------|
| `SSH_PRIVATE_KEY` | приватный SSH-ключ для `root@5.35.103.48` (публичная часть — в authorized_keys сервера) |

## 2. Repository variables
| Имя | Значение |
|-----|----------|
| `DEPLOY_PROD_ENABLED` | не задавать (или `false`) пока обкатываем test; `true` — включить деплой prod |

## 3. Environments → секрет `DOTENV`
Создать два Environment: **`test`** и **`prod`**. В каждом — один секрет **`DOTENV`**
с ПОЛНЫМ содержимым .env окружения (значения ниже заполнить своими).

### Environment `test` → секрет `DOTENV`
```dotenv
COMPOSE_PROJECT_NAME=cvtailor-test
WEB_PORT=28080
# БД в общем PostgreSQL. DB_PASSWORD = CVTAILOR_TEST_DB_PASSWORD в shared-postgres
DB_USER=cvtailor_test
DB_NAME=cvtailor_test
DB_PASSWORD=<пароль БД cvtailor_test>
JWT_SECRET_KEY=<секрет JWT test>
OPENAI_API_KEY=<ключ провайдера (OpenRouter/polza/OpenAI)>
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
FRONTEND_URL=https://cvtailor.test.vniknu.ru
BACKEND_URL=https://cvtailor.test.vniknu.ru
CONSENT_VERSION=2026-06-24
BOOTSTRAP_ADMIN_EMAIL=<email админа>
SMARTCAPTCHA_SERVER_KEY=<серверный ключ SmartCaptcha>
VITE_SMARTCAPTCHA_SITEKEY=<клиентский sitekey SmartCaptcha>
YANDEX_CLIENT_ID=<...>
YANDEX_CLIENT_SECRET=<...>
VK_CLIENT_ID=<...>
VK_CLIENT_SECRET=<...>
EMAIL_HTTP_ENDPOINT=https://postbox.cloud.yandex.net
EMAIL_HTTP_KEY_ID=
EMAIL_HTTP_SECRET=
SMTP_FROM=noreply@cvtailor.ru
# Т-Банк: на test — ДЕМО-терминал
TINKOFF_TERMINAL_KEY=1783498090224DEMO
TINKOFF_PASSWORD=<демо-пароль Т-Банка>
TINKOFF_API_URL=https://securepay.tinkoff.ru/v2/
TINKOFF_TAXATION=usn_income
TINKOFF_VAT=none
```

### Environment `prod` → секрет `DOTENV`
Отличия от test: имя/порт/база/URL и БОЕВЫЕ креды Т-Банка.
```dotenv
COMPOSE_PROJECT_NAME=cvtailor-prod
WEB_PORT=18080
DB_USER=cvtailor_prod
DB_NAME=cvtailor_prod
DB_PASSWORD=<пароль БД cvtailor_prod>
JWT_SECRET_KEY=<секрет JWT prod>
OPENAI_API_KEY=<ключ провайдера (OpenRouter/polza/OpenAI)>
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=openai/gpt-4o-mini
FRONTEND_URL=https://cvtailor.vniknu.ru
BACKEND_URL=https://cvtailor.vniknu.ru
CONSENT_VERSION=2026-06-24
BOOTSTRAP_ADMIN_EMAIL=<email админа>
SMARTCAPTCHA_SERVER_KEY=<...>
VITE_SMARTCAPTCHA_SITEKEY=<...>
YANDEX_CLIENT_ID=<...>
YANDEX_CLIENT_SECRET=<...>
VK_CLIENT_ID=<...>
VK_CLIENT_SECRET=<...>
EMAIL_HTTP_ENDPOINT=https://postbox.cloud.yandex.net
EMAIL_HTTP_KEY_ID=
EMAIL_HTTP_SECRET=
SMTP_FROM=noreply@cvtailor.ru
# Т-Банк: БОЕВЫЕ креды из ЛК
TINKOFF_TERMINAL_KEY=<боевой terminal key>
TINKOFF_PASSWORD=<боевой пароль>
TINKOFF_API_URL=https://securepay.tinkoff.ru/v2/
TINKOFF_TAXATION=usn_income
TINKOFF_VAT=none
```

> `DB_PASSWORD` каждого окружения ДОЛЖЕН совпадать с паролем роли в общем PostgreSQL
> (секрет `SHARED_POSTGRES_DOTENV` в репозитории ReviewLens).
