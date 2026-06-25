# Запуск и перезагрузка проекта

Всё работает через Docker Compose. Команды выполняются из корня проекта:

```bash
cd /Users/oberezhinskiy/Documents/work/my_lab/cv-tailor
```

## Адреса после запуска

| Что | URL |
|-----|-----|
| Приложение (через nginx) | http://localhost:18080 |
| Backend напрямую | http://localhost:18001 · Swagger: http://localhost:18001/docs |
| Frontend dev напрямую | http://localhost:15174 |

Postgres и Redis наружу не проброшены (только внутри сети compose).

## Первый запуск / полная пересборка

```bash
docker compose up --build -d
```

- Образы собираются, контейнеры стартуют в фоне.
- Миграции БД (`alembic upgrade head`) применяются **автоматически** при старте backend.
- Проверка:

```bash
docker compose ps
curl http://localhost:18080/api/health      # {"status":"ok"}
```

## Перезагрузка

### Простой перезапуск (без пересборки, код не менялся)

```bash
docker compose restart
```

### После изменения кода backend

```bash
docker compose build backend worker
docker compose up -d backend worker
docker compose restart nginx        # ⚠️ обязательно — см. ниже
```

### После изменения кода frontend

```bash
docker compose build frontend
docker compose up -d frontend
docker compose restart nginx
```

### Пересобрать всё сразу

```bash
docker compose up --build -d
docker compose restart nginx
```

> ⚠️ **Почему `restart nginx`.** Когда контейнер backend/frontend пересоздаётся, он
> получает новый внутренний IP. nginx резолвит upstream один раз при старте и держит
> старый IP → отдаёт **502 Bad Gateway**. `docker compose restart nginx` заставляет
> его перечитать адреса. Если видите 502 после пересборки — это оно.

## Остановка

```bash
docker compose down        # остановить (данные БД в volume сохраняются)
docker compose down -v      # + удалить volume с данными БД (полный сброс)
```

## Логи

```bash
docker compose logs -f backend      # следить за backend
docker compose logs -f nginx
docker compose logs --tail 50 worker
```

## Секреты (OpenAI, OAuth, SMTP, капча)

Лежат в корневом `.env` (он в `.gitignore`, в репозиторий не попадает). Compose
подставляет их в сервисы при `up`. Полный список переменных и маппинг — в
[`backend/.env.example`](backend/.env.example).

После изменения `.env`:

```bash
docker compose up -d                # пересоздаст контейнеры с новыми переменными
docker compose restart nginx
```

Без секретов всё работает в dev-режиме: код подтверждения почты печатается в логи
backend, OAuth отдаёт 503, капча пропускается, генерация резюме идёт по эвристике
(с `OPENAI_API_KEY` — реальная AI-генерация).

## Миграции БД (обычно не нужно — применяются авто)

```bash
docker compose exec backend alembic current        # текущая ревизия
docker compose exec backend alembic upgrade head    # применить вручную
docker compose exec backend alembic downgrade -1    # откатить на шаг
```

## Локальная разработка без пересборки образов

**Frontend с HMR** (backend остаётся в docker):

```bash
cd frontend
npm install
echo 'VITE_API_BASE_URL=http://localhost:18080/api' > .env.local
npm run dev          # http://localhost:5173
```

**Backend без docker** (нужны локальные Postgres/Redis или их адреса):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql+psycopg://cv_tailor:cv_tailor@localhost:5432/cv_tailor
alembic upgrade head
uvicorn app.main:app --reload      # http://localhost:8000
```
