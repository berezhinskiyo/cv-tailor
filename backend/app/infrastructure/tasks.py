from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_app = Celery("cv_tailor", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task
def noop_task() -> str:
    return "ok"

