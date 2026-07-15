# Деплой cv-tailor — два окружения на общем сервере

Сервер: `root@109.73.197.92`. На нём живут 4 стека (cvtailor + reviewlens, test/prod)
за **единым edge-Caddy** (владеет 80/443, авто-TLS Let's Encrypt) и с **единым
PostgreSQL** (общий инстанс, у каждого окружения своя база). Стек cv-tailor отдаёт
nginx на loopback-порт, edge проксирует домен на этот порт.

| Окружение | Ветка  | Домен                       | Каталог             | Loopback-порт | База в общем PG |
|-----------|--------|-----------------------------|---------------------|---------------|-----------------|
| test      | `test` | `cvtailor.test.vniknu.ru`   | `/opt/cvtailor-test`| `127.0.0.1:28080` | `cvtailor_test` |
| prod      | `prod` | `cvtailor.vniknu.ru`        | `/opt/cvtailor-prod`| `127.0.0.1:18080` | `cvtailor_prod` |

## Каскад релизов (`.github/workflows/deploy.yml`)

```
push main  → force-push в test  (→ деплой TEST)
push test  → деплой TEST         → (при DEPLOY_PROD_ENABLED=true) force-push в prod
push prod  → деплой PROD          (при DEPLOY_PROD_ENABLED=true)
```

- Секрет репозитория **`SSH_PRIVATE_KEY`** — вход на сервер.
- Repo-переменная **`DEPLOY_PROD_ENABLED`**: пока не `true`, любой push катит **только TEST**.

## Общая инфраструктура сервера (общий PostgreSQL + edge-Caddy)

Поднимаются один раз ручным запуском workflow в репозитории **ReviewLens**
(Actions → Deploy → Run workflow → галочка bootstrap): останавливает старые стеки,
поднимает `/opt/shared-postgres` (сеть `shared`, базы `cvtailor_{prod,test}` /
`reviewlens_{prod,test}`) и `/opt/edge` (80/443 + TLS на 4 домена). Отдельного действия
для cv-tailor тут не нужно.

## Секреты cv-tailor — всё в GitHub

Полный список констант — в **`GITHUB_SECRETS.md`**. Кратко:
- Repo secret `SSH_PRIVATE_KEY`, repo variable `DEPLOY_PROD_ENABLED` (пока не задавать).
- Environments `test` и `prod`, в каждом секрет `DOTENV` с полным .env окружения
  (WEB_PORT, DB_USER/DB_NAME/DB_PASSWORD, JWT, OAuth, Т-Банк и т.д.).
- `DB_PASSWORD` окружения = пароль роли в общем PostgreSQL
  (`CVTAILOR_TEST_DB_PASSWORD` / `CVTAILOR_PROD_DB_PASSWORD` в `SHARED_POSTGRES_DOTENV`).

OAuth: redirect URI обоих доменов добавить в приложениях Яндекс/VK.
Деплой — пуш в ветку; `.env` пишется на сервер из секрета `DOTENV` автоматически.

## Важно
- **Изоляция**: у test и prod разные `COMPOSE_PROJECT_NAME` (сети/контейнеры) и разные
  базы+роли в общем PG (test не видит prod). Redis у каждого стека свой.
- **Миграции** применяются автоматически при старте backend (`alembic upgrade head`
  в `Dockerfile CMD`).
- Стек требует внешнюю сеть `shared` — сначала должен быть поднят `shared-postgres`.
