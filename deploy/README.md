# Деплой cv-tailor — два окружения на общем сервере

Сервер: `root@5.35.103.48`. На нём живут 4 стека (cvtailor + reviewlens, test/prod)
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

## Общая инфраструктура сервера (один раз, файлы — в репозитории ReviewLens/deploy)

- **`shared-postgres`** — единый PostgreSQL (`/opt/shared-postgres`), создаёт сеть `shared`
  и базы `cvtailor_{prod,test}` / `reviewlens_{prod,test}`.
- **`edge`** — единый Caddy (`/opt/edge`), 80/443 + TLS, роутит все 4 домена на loopback-порты.

Поднимаются до первого деплоя (см. `ReviewLens/deploy/README.md`, шаги 0–1).

## Бутстрап cv-tailor-окружений

1. **`.env` каждого окружения** (в git нет, деплой не трогает):
   ```bash
   mkdir -p /opt/cvtailor-test /opt/cvtailor-prod
   nano /opt/cvtailor-test/.env     # deploy/env.test.example: WEB_PORT=28080, DB_*=cvtailor_test, ДЕМО-креды Т-Банка
   nano /opt/cvtailor-prod/.env     # deploy/env.prod.example: WEB_PORT=18080, DB_*=cvtailor_prod, БОЕВЫЕ креды Т-Банка
   ```
   `DB_PASSWORD` окружения должен совпадать с соответствующим паролем в
   `/opt/shared-postgres/.env` (`CVTAILOR_TEST_DB_PASSWORD` / `CVTAILOR_PROD_DB_PASSWORD`).
   Разные `JWT_SECRET_KEY` для test и prod.

2. **OAuth**: redirect URI обоих доменов добавить в приложениях Яндекс/VK.

3. Первый деплой — пуш в ветку (каталог создаётся `git clone`, но `.env` должен уже лежать).

## Важно
- **Изоляция**: у test и prod разные `COMPOSE_PROJECT_NAME` (сети/контейнеры) и разные
  базы+роли в общем PG (test не видит prod). Redis у каждого стека свой.
- **Миграции** применяются автоматически при старте backend (`alembic upgrade head`
  в `Dockerfile CMD`).
- Стек требует внешнюю сеть `shared` — сначала должен быть поднят `shared-postgres`.
