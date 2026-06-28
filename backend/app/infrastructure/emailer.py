"""Отправка кода подтверждения e-mail.

Порядок выбора транспорта:
1. HTTP-API Yandex Cloud Postbox (AWS SES-совместимый SendEmail, подпись SigV4) —
   если задан EMAIL_HTTP_ENDPOINT (+ EMAIL_HTTP_KEY_ID / EMAIL_HTTP_SECRET).
2. SMTP — если задан SMTP_HOST.
3. Иначе код печатается в консоль (dev-режим), регистрация работает end-to-end.
"""

import hashlib
import hmac
import json
import logging
import smtplib
import ssl
from datetime import datetime, timezone
from email.message import EmailMessage

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUBJECT = "Код подтверждения CV Tailor"


def _body(code: str) -> str:
    return f"Ваш код подтверждения: {code}\n\nКод действует 15 минут."


# ── HTTP-API Yandex Postbox (SES-совместимый, AWS SigV4) ─────────────────────
def _host(endpoint: str) -> str:
    return endpoint.removeprefix("https://").removeprefix("http://").split("/")[0]


def _sigv4_key(secret: str, date: str, region: str, service: str) -> bytes:
    def sign(key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode(), hashlib.sha256).digest()

    return sign(sign(sign(sign(f"AWS4{secret}".encode(), date), region), service), "aws4_request")


def _send_via_http(email: str, code: str) -> None:
    """Yandex Cloud Postbox — AWS SES API v2 (SendEmail), подпись AWS SigV4."""
    base = settings.email_http_endpoint.strip().rstrip("/")
    key_id = settings.email_http_key_id.strip()
    secret = settings.email_http_secret.strip()
    from_addr = (settings.smtp_from or "noreply@cvtailor.ru").strip()

    service = "ses"
    region = "ru-central1"
    canonical_uri = "/v2/email/outbound-emails"
    host = _host(base)

    body = json.dumps(
        {
            "FromEmailAddress": from_addr,
            "Destination": {"ToAddresses": [email]},
            "Content": {
                "Simple": {
                    "Subject": {"Data": SUBJECT, "Charset": "UTF-8"},
                    "Body": {"Text": {"Data": _body(code), "Charset": "UTF-8"}},
                }
            },
        }
    )

    now = datetime.now(timezone.utc)
    amz_date = now.strftime("%Y%m%dT%H%M%SZ")
    date_stamp = now.strftime("%Y%m%d")

    content_hash = hashlib.sha256(body.encode()).hexdigest()
    canonical_headers = (
        f"content-type:application/json\nhost:{host}\nx-amz-date:{amz_date}\n"
    )
    signed_headers = "content-type;host;x-amz-date"
    canonical_request = "\n".join(
        ["POST", canonical_uri, "", canonical_headers, signed_headers, content_hash]
    )

    credential_scope = f"{date_stamp}/{region}/{service}/aws4_request"
    string_to_sign = "\n".join(
        [
            "AWS4-HMAC-SHA256",
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode()).hexdigest(),
        ]
    )

    signing_key = _sigv4_key(secret, date_stamp, region, service)
    signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
    auth_header = (
        f"AWS4-HMAC-SHA256 Credential={key_id}/{credential_scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )

    with httpx.Client(timeout=15) as client:
        resp = client.post(
            f"{base}{canonical_uri}",
            content=body.encode(),
            headers={
                "Content-Type": "application/json",
                "X-Amz-Date": amz_date,
                "Authorization": auth_header,
            },
        )
    if resp.status_code >= 400:
        logger.error("Postbox SESv2 %s: %s", resp.status_code, resp.text[:300])
    resp.raise_for_status()


# ── SMTP ─────────────────────────────────────────────────────────────────────
def _send_via_smtp(email: str, code: str) -> None:
    use_ssl = settings.smtp_ssl or settings.smtp_port == 465
    message = EmailMessage()
    message["From"] = settings.smtp_from or settings.smtp_user
    message["To"] = email
    message["Subject"] = SUBJECT
    message.set_content(_body(code))

    if use_ssl:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, timeout=15, context=ctx) as smtp:
            smtp.ehlo()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as smtp:
            smtp.ehlo()
            smtp.starttls(context=ssl.create_default_context())
            smtp.ehlo()
            if settings.smtp_user:
                smtp.login(settings.smtp_user, settings.smtp_password)
            smtp.send_message(message)


def send_email_code(email: str, code: str) -> None:
    if settings.email_http_endpoint.strip():
        try:
            _send_via_http(email, code)
            return
        except Exception:
            logger.exception("Postbox HTTP send failed for %s", email)
            raise
    if settings.smtp_host.strip():
        try:
            _send_via_smtp(email, code)
            return
        except Exception:
            logger.exception("SMTP send failed for %s", email)
            raise
    print(f"[EMAIL DEV] {email}: {code}")
