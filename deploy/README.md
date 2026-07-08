# Деплой cv-tailor — два окружения на одном сервере

Сервер: `root@5.35.103.48`. TLS и домены обслуживает **общий обратный прокси**
сервера (владеет портами 80/443). Каждое окружение — отдельный docker-compose стек,
который отдаёт свой nginx на loopback-порт; общий прокси проксирует домен на этот порт.

| Окружение | Ветка  | Домен                       | Каталог             | Loopback-порт |
|-----------|--------|-----------------------------|---------------------|---------------|
| test      | `test` | `cvtailor.test.vniknu.ru`   | `/opt/cvtailor-test`| `127.0.0.1:28080` |
| prod      | `prod` | `cvtailor.vniknu.ru`        | `/opt/cvtailor-prod`| `127.0.0.1:18080` |

## Каскад релизов (GitHub Actions, `.github/workflows/deploy.yml`)

```
push main  → force-push в test  ─┐
push test  → деплой TEST         ─┴→ force-push в prod
push prod  → деплой PROD
```

Требуется секрет репозитория **`SSH_PRIVATE_KEY`** (приватный ключ, чья публичная
часть лежит в `~/.ssh/authorized_keys` на 5.35.103.48).

**Предохранитель прода.** Промоушен `test → prod` и деплой PROD выполняются только
при включённой repo-переменной **`DEPLOY_PROD_ENABLED=true`**
(Settings → Secrets and variables → Actions → Variables). Пока флаг не выставлен,
любой push катит **только TEST** — прод не трогается. Это позволяет сперва обкатать
`cvtailor.test.vniknu.ru`, а прод включить осознанно, когда `/opt/cvtailor-prod/.env`
и домен `cvtailor.vniknu.ru` в прокси готовы.

## Разовый бутстрап сервера (делается вручную один раз)

1. **Docker + compose-плагин** должны быть установлены на сервере.

2. **`.env` каждого окружения** (в git их нет, деплой их не трогает):

   ```bash
   mkdir -p /opt/cvtailor-test /opt/cvtailor-prod
   # заполнить значениями (шаблоны — deploy/env.test.example / env.prod.example):
   nano /opt/cvtailor-test/.env     # WEB_PORT=28080, домен test, ДЕМО-креды Т-Банка
   nano /opt/cvtailor-prod/.env     # WEB_PORT=18080, домен prod, БОЕВЫЕ креды Т-Банка
   ```
   Обязательно задать разные `POSTGRES_PASSWORD` и `JWT_SECRET_KEY` для test и prod.

3. **Прописать два домена в общий прокси** (см. ниже) и перезагрузить прокси.

4. Первый деплой — пуш в соответствующую ветку (или запуск workflow вручную).
   Каталог `/opt/cvtailor-*` создаётся автоматически (`git clone`), но `.env`
   должен уже лежать — иначе деплой упадёт с понятной ошибкой.

## Vhost для общего прокси

### Вариант A — общий прокси на Caddy
Добавить в общий `Caddyfile`:

```caddy
cvtailor.vniknu.ru {
	encode gzip
	reverse_proxy 127.0.0.1:18080
}

cvtailor.test.vniknu.ru {
	encode gzip
	reverse_proxy 127.0.0.1:28080
}
```
Caddy сам выпустит и продлит сертификаты Let's Encrypt (DNS уже указывает на сервер).
Перезагрузка: `caddy reload` (или `docker exec <caddy> caddy reload ...`).

### Вариант B — общий прокси на nginx
Выпустить сертификаты (`certbot certonly` для обоих доменов) и добавить server-блоки:

```nginx
server {
    listen 80;
    server_name cvtailor.vniknu.ru cvtailor.test.vniknu.ru;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name cvtailor.vniknu.ru;
    ssl_certificate     /etc/letsencrypt/live/cvtailor.vniknu.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cvtailor.vniknu.ru/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
server {
    listen 443 ssl;
    server_name cvtailor.test.vniknu.ru;
    ssl_certificate     /etc/letsencrypt/live/cvtailor.test.vniknu.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/cvtailor.test.vniknu.ru/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:28080;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Перезагрузка: `nginx -t && nginx -s reload`.

## Важно
- **OAuth**: redirect URI обоих доменов нужно добавить в приложениях Яндекс/VK,
  иначе вход через OAuth вернёт ошибку.
- **Изоляция БД**: у test и prod разные `COMPOSE_PROJECT_NAME` → разные volume/сети,
  данные не пересекаются.
- **Миграции** применяются автоматически при старте backend (`alembic upgrade head`
  в `Dockerfile CMD`).
