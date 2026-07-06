"""Отправка email. Реализация вынесена в общий пакет auth-billing-core (async).

Тонкий реэкспорт для обратной совместимости импортов проекта.
"""
from authbilling.emailer import send_email, send_email_code  # noqa: F401
