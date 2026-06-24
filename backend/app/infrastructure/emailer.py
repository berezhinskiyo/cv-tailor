"""Отправка кода подтверждения e-mail.

Если SMTP не настроен (нет SMTP_HOST) — код печатается в консоль (dev-режим),
поэтому регистрация работает end-to-end даже без почтового провайдера.
"""

import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SUBJECT = "Код подтверждения CV Tailor"


def _body(code: str) -> str:
    return f"Ваш код подтверждения: {code}\n\nКод действует 15 минут."


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
    if not settings.smtp_host.strip():
        print(f"[EMAIL DEV] {email}: {code}")
        return
    try:
        _send_via_smtp(email, code)
    except Exception:
        logger.exception("Email send failed for %s", email)
        raise
