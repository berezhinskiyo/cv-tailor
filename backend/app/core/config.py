from functools import lru_cache

from authbilling import AuthBillingSettings, configure
from pydantic import Field


class Settings(AuthBillingSettings):
    """Настройки CV Tailor. Общие поля auth/billing наследуются из AuthBillingSettings."""

    app_name: str = "AI Resume Tailor"
    # Async-драйвер: sqlite+aiosqlite локально, postgresql+asyncpg в проде.
    database_url: str = "sqlite+aiosqlite:///./cv_tailor.db"
    jwt_secret_key: str = "change-me"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    free_user_analysis_limit: int = 3
    free_anonymous_analysis_limit: int = 1

    # Переопределяем дефолты под бренд
    consent_version: str = "2026-06-24"
    smtp_from: str = "noreply@cvtailor.ru"
    email_subject: str = "Код подтверждения CV Tailor"
    # Приложение Яндекс ID настроено только на доступ к email — не просим login:info,
    # иначе Яндекс вернёт invalid_scope.
    yandex_scope: str = "login:email"

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://localhost",
            "http://127.0.0.1:5173",
        ]
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

# Регистрируем настройки проекта в пакете auth-billing-core.
configure(settings)
