FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# git нужен для pip-установки общего пакета authbilling из GitHub (git+https)
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Сертификаты Russian Trusted CA (Минцифры) — для TLS к API Т-Банка (securepay.tinkoff.ru).
# Ставим и в системное хранилище, и в bundle certifi (его использует httpx).
RUN set -eux; \
    apt-get update; apt-get install -y --no-install-recommends ca-certificates curl; \
    curl -fsSL https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt -o /usr/local/share/ca-certificates/russian_trusted_root_ca.crt; \
    curl -fsSL https://gu-st.ru/content/lending/russian_trusted_sub_ca_pem.crt  -o /usr/local/share/ca-certificates/russian_trusted_sub_ca.crt; \
    update-ca-certificates; \
    cat /usr/local/share/ca-certificates/russian_trusted_root_ca.crt \
        /usr/local/share/ca-certificates/russian_trusted_sub_ca.crt \
        >> "$(python -c 'import certifi; print(certifi.where())')"; \
    rm -rf /var/lib/apt/lists/*

COPY . .

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
