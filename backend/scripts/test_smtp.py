#!/usr/bin/env python3
"""Автономная проверка/отладка отправки почты через SMTP.

Поддерживает два сценария Яндекса:

1. Yandex Cloud Postbox (рекомендуется для сервисов) —
   https://yandex.cloud/ru/docs/postbox/quickstart
     - сервер  : postbox.cloud.yandex.net
     - порт    : 587 (STARTTLS) или 465 (SMTPS)
     - логин   : ИДЕНТИФИКАТОР API-ключа (scope yc.postbox.send)
     - пароль  : секретная часть API-ключа
     - FROM    : подтверждённый по DKIM адрес вашего домена (НЕ равен логину!)

2. Обычная Яндекс.Почта (smtp.yandex.ru) —
     - логин/FROM : ваш адрес @yandex.ru (FROM должен совпадать с логином)
     - пароль     : пароль приложения (при включённой 2FA)

Скрипт НЕ зависит от приложения: читает те же переменные окружения, что и backend
(SMTP_HOST/PORT/SSL/USER/PASSWORD/FROM), и реально отправляет письмо, печатая весь
диалог с сервером (smtplib debug).

Примеры:

    # Postbox: всё из .env, отправить себе
    python backend/scripts/test_smtp.py --to you@example.com

    # Postbox: пресет сервера/порта + ключи флагами
    python backend/scripts/test_smtp.py --postbox \
        --to you@example.com \
        --user <API_KEY_ID> --password <API_KEY_SECRET> \
        --from noreply@ваш-домен.ru

    # Обычная Яндекс.Почта
    python backend/scripts/test_smtp.py \
        --to you@example.com \
        --host smtp.yandex.ru --port 465 --ssl \
        --user my@yandex.ru --password APP_PASSWORD --from my@yandex.ru

Коды выхода: 0 — письмо принято сервером, 1 — ошибка (см. вывод).
"""

from __future__ import annotations

import argparse
import os
import smtplib
import ssl
import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path

POSTBOX_HOST = "postbox.cloud.yandex.net"


def load_env_file(path: Path) -> None:
    """Минимальный парсер .env: KEY=VALUE; не затирает уже выставленное окружение."""
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def env_bool(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def find_default_env() -> Path:
    # backend/scripts/test_smtp.py -> корень проекта на два уровня выше backend/
    return Path(__file__).resolve().parents[2] / ".env"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Тест отправки почты через SMTP (Yandex Postbox / Яндекс.Почта)")
    p.add_argument("--to", help="кому отправить тестовое письмо")
    p.add_argument("--env-file", help="путь к .env (по умолчанию — .env в корне проекта)")
    p.add_argument(
        "--postbox",
        action="store_true",
        help=f"пресет Yandex Cloud Postbox: host={POSTBOX_HOST}, порт 587/STARTTLS (или 465 c --ssl)",
    )
    p.add_argument("--host", help="SMTP_HOST")
    p.add_argument("--port", type=int, help="SMTP_PORT (465 для SSL, 587 для STARTTLS)")
    p.add_argument("--ssl", dest="ssl", action="store_true", help="использовать SSL/SMTPS (порт 465)")
    p.add_argument("--no-ssl", dest="ssl", action="store_false", help="использовать STARTTLS (порт 587)")
    p.set_defaults(ssl=None)
    p.add_argument("--user", help="SMTP_USER (Postbox: ID API-ключа; почта: адрес @yandex.ru)")
    p.add_argument("--password", help="SMTP_PASSWORD (Postbox: секрет API-ключа; почта: пароль приложения)")
    p.add_argument("--from", dest="from_addr", help="SMTP_FROM (Postbox: подтверждённый адрес домена)")
    p.add_argument("--subject", default="CV Tailor SMTP test", help="тема письма")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    env_path = Path(args.env_file) if args.env_file else find_default_env()
    load_env_file(env_path)
    print(f"[i] .env: {env_path} ({'найден' if env_path.is_file() else 'не найден, беру только окружение'})")

    host = args.host or os.environ.get("SMTP_HOST", "")
    if args.postbox and not host:
        host = POSTBOX_HOST

    # порт: флаг > .env > дефолт (для Postbox STARTTLS 587)
    if args.port:
        port = args.port
    elif os.environ.get("SMTP_PORT"):
        port = int(os.environ["SMTP_PORT"])
    else:
        port = 587

    use_ssl = args.ssl if args.ssl is not None else (env_bool("SMTP_SSL") or port == 465)
    user = args.user or os.environ.get("SMTP_USER", "")
    password = args.password or os.environ.get("SMTP_PASSWORD", "")
    from_addr = args.from_addr or os.environ.get("SMTP_FROM", "") or user
    to_addr = args.to or os.environ.get("SMTP_USER", "")

    is_postbox = "postbox" in host
    is_yandex_mail = "yandex" in host and not is_postbox

    print("[i] Параметры подключения:")
    print(f"    PROVIDER = {'Yandex Cloud Postbox' if is_postbox else ('Яндекс.Почта' if is_yandex_mail else 'generic SMTP')}")
    print(f"    HOST     = {host or '(пусто!)'}")
    print(f"    PORT     = {port}")
    print(f"    SSL      = {use_ssl} ({'SMTPS/465' if use_ssl else 'STARTTLS'})")
    print(f"    USER     = {user or '(пусто)'}")
    print(f"    PASSWORD = {'*' * len(password) if password else '(пусто!)'}")
    print(f"    FROM     = {from_addr or '(пусто!)'}")
    print(f"    TO       = {to_addr or '(пусто!)'}")

    problems = []
    if not host:
        problems.append("SMTP_HOST пуст — отправка невозможна (backend уйдёт в dev-режим и напечатает код в лог).")
    if not to_addr:
        problems.append("Не задан получатель: укажите --to.")
    if not user or not password:
        problems.append("Пусты USER/PASSWORD — для Postbox это ID и секрет API-ключа (scope yc.postbox.send).")
    if is_yandex_mail and user and from_addr and user.lower() != from_addr.lower():
        problems.append(
            f"Для обычной Яндекс.Почты FROM ({from_addr}) должен совпадать с USER ({user})."
        )
    if is_postbox and "@" in user:
        problems.append(
            "Похоже, в USER указан e-mail, а для Postbox USER — это ИДЕНТИФИКАТОР API-ключа, не адрес."
        )
    if is_postbox and (not from_addr or "@" not in from_addr):
        problems.append(
            "Для Postbox FROM должен быть подтверждённым по DKIM адресом вашего домена (напр. noreply@домен.ru)."
        )
    if problems:
        print("\n[!] Замечания по конфигурации:")
        for pr in problems:
            print(f"    - {pr}")
        if not host or not to_addr:
            return 1

    # Письмо: multipart text + html (как в примере Postbox)
    message = MIMEMultipart("alternative")
    message["From"] = from_addr
    message["To"] = to_addr
    message["Subject"] = args.subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid()
    text = (
        "Это тестовое письмо от backend/scripts/test_smtp.py.\n"
        "Если вы его получили — SMTP настроен корректно."
    )
    html = (
        "<html><body>"
        "<p>Это <b>тестовое письмо</b> от <code>backend/scripts/test_smtp.py</code>.</p>"
        "<p>Если вы его получили — SMTP настроен корректно.</p>"
        "</body></html>"
    )
    message.attach(MIMEText(text, "plain", "utf-8"))
    message.attach(MIMEText(html, "html", "utf-8"))

    ctx = ssl.create_default_context()
    print("\n[i] Соединяюсь с сервером... (ниже — полный диалог SMTP)\n" + "-" * 60)
    try:
        if use_ssl:
            with smtplib.SMTP_SSL(host, port, timeout=20, context=ctx) as smtp:
                smtp.set_debuglevel(1)
                smtp.ehlo()
                if user:
                    smtp.login(user, password)
                smtp.send_message(message)
        else:
            with smtplib.SMTP(host, port, timeout=20) as smtp:
                smtp.set_debuglevel(1)
                smtp.ehlo()
                smtp.starttls(context=ctx)
                smtp.ehlo()
                if user:
                    smtp.login(user, password)
                smtp.send_message(message)
    except smtplib.SMTPAuthenticationError as e:
        print("-" * 60)
        print(f"\n[x] Ошибка аутентификации: {e}")
        if is_postbox:
            print("    Postbox: USER — ID API-ключа, PASSWORD — его секрет, scope должен быть yc.postbox.send.")
        else:
            print("    Яндекс.Почта: включите доступ по IMAP/SMTP и используйте ПАРОЛЬ ПРИЛОЖЕНИЯ (при 2FA).")
        return 1
    except (smtplib.SMTPException, OSError) as e:
        print("-" * 60)
        print(f"\n[x] Ошибка отправки: {type(e).__name__}: {e}")
        if is_postbox:
            print(f"    Проверьте host={POSTBOX_HOST}, порт 587(STARTTLS)/465(SMTPS),")
            print("    и что FROM-адрес прошёл проверку DKIM (статус Success на странице адреса).")
        else:
            print("    Проверьте host/port/ssl: smtp.yandex.ru -> 465+SSL или 587+STARTTLS.")
        return 1

    print("-" * 60)
    print(f"\n[\u2713] Письмо принято сервером и отправлено на {to_addr}.")
    if is_postbox:
        print("    Если не пришло — проверьте «Спам» и что домен FROM подтверждён по DKIM (Success).")
    else:
        print("    Если не пришло — проверьте «Спам» и совпадение FROM с USER.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
