from __future__ import annotations

from collections import defaultdict

from redis import Redis
from redis.exceptions import RedisError

from app.core.config import get_settings

settings = get_settings()
_memory_limits: dict[str, int] = defaultdict(int)


class LimitService:
    def __init__(self) -> None:
        try:
            self.redis = Redis.from_url(settings.redis_url, decode_responses=True)
            self.redis.ping()
        except RedisError:
            self.redis = None

    def assert_anonymous_limit(self, anonymous_id: str | None) -> None:
        if not anonymous_id:
            raise ValueError("Для анонимного анализа нужен anonymous_id.")
        usage = self._increment_and_get(f"anon:{anonymous_id}")
        if usage > settings.free_anonymous_analysis_limit:
            raise PermissionError("Требуется подписка.")

    def assert_user_limit(self, analysis_count: int, subscription_type: str) -> None:
        if subscription_type != "free":
            return
        if analysis_count >= settings.free_user_analysis_limit:
            raise PermissionError("Требуется подписка.")

    def _increment_and_get(self, key: str) -> int:
        if self.redis is not None:
            value = self.redis.incr(key)
            self.redis.expire(key, 60 * 60 * 24 * 30)
            return int(value)
        _memory_limits[key] += 1
        return _memory_limits[key]

