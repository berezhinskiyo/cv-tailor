# AI Resume Tailor

MVP веб-приложения для адаптации резюме под конкретную вакансию.

Сервис умеет:
- анализировать соответствие резюме вакансии;
- считать процент совпадения по навыкам;
- показывать отсутствующие навыки;
- генерировать улучшенную версию резюме;
- генерировать сопроводительное письмо;
- экспортировать результат в PDF.

## Стек

### Backend

- Python 3.12
- FastAPI
- SQLAlchemy 2
- Alembic
- PostgreSQL
- Redis
- Celery
- OpenAI API
- JWT (access + refresh) auth
- OAuth (Яндекс / VK)
- Яндекс SmartCaptcha
- ReportLab

### Frontend

- React 18
- TypeScript
- Vite
- React Router
- Собственная CSS-дизайн-система (без UI-фреймворка)

### Infrastructure

- Docker
- Docker Compose
- Nginx
- GitHub Actions

## Структура проекта

```text
cv-tailor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── domain/
│   │   ├── infrastructure/
│   │   ├── repositories/
│   │   └── services/
│   ├── alembic/
│   └── tests/
├── frontend/
├── nginx/
└── docker-compose.yml
```

## Архитектура

Backend организован по слоям:

- `api` - FastAPI-роуты и зависимости.
- `services` - бизнес-логика анализа, лимитов и PDF.
- `repositories` - доступ к базе данных.
- `domain` - ORM-модели и Pydantic-схемы.
- `infrastructure` - интеграции с OpenAI и Celery.
- `core` - конфиг, база, security.

## Как работает анализ

1. Из текста вакансии извлекаются навыки.
2. Из текста резюме извлекаются навыки.
3. Рассчитывается `score = matched_skills / vacancy_skills * 100`.
4. Формируется список отсутствующих навыков.
5. В OpenAI отправляется запрос на улучшение резюме и генерацию cover letter.
6. Если `OPENAI_API_KEY` не задан, включается локальный fallback, и приложение всё равно работает end-to-end.

## Ограничения бесплатного тарифа

- Анонимный пользователь: `1` анализ.
- Авторизованный пользователь с `subscription_type=free`: `3` анализа.
- После превышения лимита API возвращает ошибку: `Требуется подписка.`

## Быстрый старт через Docker

### 1. Запуск

```bash
docker compose up --build
```

После старта будут доступны:

- frontend: [http://localhost:5173](http://localhost:5173)
- backend API: [http://localhost:8000](http://localhost:8000)
- nginx entrypoint: [http://localhost](http://localhost)

### 2. Что запускается

- `postgres` - основная БД
- `redis` - кэш и broker
- `backend` - FastAPI + Alembic migration on startup
- `worker` - Celery worker
- `frontend` - Vite dev server
- `nginx` - reverse proxy

## Локальный запуск без Docker

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## Переменные окружения

### Backend

См. [backend/.env.example](/Users/oberezhinskiy/Documents/work/my_lab/cv-tailor/backend/.env.example)

Основные переменные:

- `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`
- `OPENAI_API_KEY`, `OPENAI_MODEL`
- `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_DAYS`
- `CONSENT_VERSION`, `BOOTSTRAP_ADMIN_EMAIL`
- `FRONTEND_URL`, `BACKEND_URL` — для OAuth redirect и возврата во фронт
- `SMARTCAPTCHA_SERVER_KEY` — серверная валидация капчи (пусто = пропуск)
- `YANDEX_CLIENT_ID/SECRET`, `VK_CLIENT_ID/SECRET` — OAuth
- `SMTP_*` — отправка кода подтверждения (пусто = код печатается в логи)

### Frontend

См. [frontend/.env.example](/Users/oberezhinskiy/Documents/work/my_lab/cv-tailor/frontend/.env.example)

- `VITE_API_BASE_URL`
- `VITE_SMARTCAPTCHA_SITEKEY` — клиентский ключ капчи (пусто = капча отключена)

## API

### Auth

Регистрация по e-mail выполняется в два шага (код подтверждения), доступ продлевается
через refresh-токен с ротацией.

- `POST /api/auth/register/request-code` — отправка кода на e-mail (+ проверка капчи)
- `POST /api/auth/register/verify` — подтверждение кода, выдача пары токенов
- `POST /api/auth/register` — прямая регистрация без кода (для API-клиентов)
- `POST /api/auth/login`
- `POST /api/auth/refresh` — ротация refresh-токена
- `POST /api/auth/logout` — отзыв refresh-токена
- `GET /api/auth/me`
- `GET /api/auth/oauth/{provider}/start` — старт OAuth (`yandex` | `vk`)
- `GET /api/auth/oauth/{provider}/callback` — обмен кода, редирект во фронт

### Resume

- `POST /api/resumes`
- `GET /api/resumes`
- `GET /api/resumes/{id}`
- `DELETE /api/resumes/{id}`

### Vacancy

- `POST /api/vacancies`
- `GET /api/vacancies`
- `GET /api/vacancies/{id}`
- `DELETE /api/vacancies/{id}`

### Analysis

- `POST /api/analysis`
- `GET /api/analysis`
- `GET /api/analysis/{id}`
- `GET /api/analysis/{id}/pdf`

## Примеры сценариев

### Анонимный анализ

`POST /api/analysis`

```json
{
  "resume_text": "Python FastAPI PostgreSQL Docker Redis",
  "vacancy_text": "Python FastAPI PostgreSQL Docker Kubernetes CI/CD",
  "anonymous_id": "demo-user-1"
}
```

### Анализ для авторизованного пользователя

```json
{
  "resume_id": 1,
  "vacancy_id": 1,
  "vacancy_text": "placeholder"
}
```

Если передан `vacancy_id`, текст вакансии берется из БД. Поле `vacancy_text` в текущем API остаётся обязательным для совместимости со схемой запроса.

## База данных

Основные сущности:

- `users`
- `resumes`
- `vacancies`
- `analyses`

Начальная миграция находится в [backend/alembic/versions/0001_initial.py](/Users/oberezhinskiy/Documents/work/my_lab/cv-tailor/backend/alembic/versions/0001_initial.py).

## Тесты

Backend-тесты:

```bash
cd backend
pytest
```

Покрыты базовые сценарии:

- регистрация пользователя;
- создание резюме и вакансии;
- запуск анализа;
- ограничение по анонимному тарифу.

## CI

GitHub Actions workflow расположен в [`.github/workflows/ci.yml`](/Users/oberezhinskiy/Documents/work/my_lab/cv-tailor/.github/workflows/ci.yml).

Он:

- устанавливает backend-зависимости;
- запускает `pytest`;
- устанавливает frontend-зависимости;
- выполняет `npm run build`.

## Текущее состояние MVP

Реализовано:

- продающий лендинг на собственной CSS-дизайн-системе (hero, демо-анализ, фичи, тарифы, футер);
- регистрация по e-mail с кодом подтверждения, вход, OAuth (Яндекс / VK);
- access + refresh токены с ротацией и отзывом (logout);
- защита регистрации Яндекс SmartCaptcha;
- личный кабинет для сохранения резюме/вакансий и запуска анализа;
- сохранение истории анализов и скачивание PDF;
- регуляторный контур: оферта, политика 152-ФЗ, контакты/реквизиты, cookie-баннер,
  версия согласия (`consent_version`), документ [COMPLIANCE_152FZ.md](/Users/oberezhinskiy/Documents/work/my_lab/cv-tailor/COMPLIANCE_152FZ.md);
- Docker Compose и базовая инфраструктура.

Ограничения текущей версии:

- список навыков извлекается эвристически по известному набору ключевых слов
  (в т.ч. `sql` ловится как подстрока `postgresql` — см. «Следующие улучшения»);
- Celery подключен как инфраструктурная заготовка, но анализ пока выполняется синхронно;
- OAuth/SMTP/капча требуют реальных ключей провайдеров (без них деградируют безопасно:
  503 для OAuth, печать кода в логи, пропуск капчи);
- полноценное покрытие 70% тестами ещё не добито.

## Следующие улучшения

- вынести анализ в фоновые задачи Celery;
- улучшить NLP-извлечение навыков;
- добавить refresh tokens и logout;
- сделать полноценную сущность `Project`;
- расширить тестовое покрытие;
- добавить наблюдаемость и rate limiting.
