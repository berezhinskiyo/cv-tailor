from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "AI Resume Tailor"
    database_url: str = "sqlite:///./cv_tailor.db"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    # Access-токен короткоживущий, доступ продлевается через refresh-токен.
    access_token_expire_minutes: int = 15
    refresh_token_days: int = 30
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    redis_url: str = "redis://localhost:6379/0"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://localhost", "http://127.0.0.1:5173"])
    free_user_analysis_limit: int = 3
    free_anonymous_analysis_limit: int = 1

    # ── Регистрация / согласие
    consent_version: str = "2026-06-24"
    bootstrap_admin_email: str = ""

    # ── Внешние URL (OAuth redirect + ссылка обратно во фронт)
    frontend_url: str = "http://localhost:5173"
    backend_url: str = "http://localhost:8000"

    # ── Капча (серверный ключ Яндекс SmartCaptcha; пусто = проверка пропускается)
    smartcaptcha_server_key: str = ""

    # ── OAuth провайдеры
    yandex_client_id: str = ""
    yandex_client_secret: str = ""
    vk_client_id: str = ""
    vk_client_secret: str = ""

    # ── Отправка email с кодом (если ничего не задано — код печатается в консоль)
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_ssl: bool = False
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = "noreply@cv-tailor.local"


@lru_cache
def get_settings() -> Settings:
    return Settings()

