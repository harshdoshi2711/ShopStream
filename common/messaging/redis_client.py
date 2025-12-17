# common/messaging/redis_client.py

import redis
from common.config.settings import get_settings

settings = get_settings()


def get_redis_client() -> redis.Redis:
    return redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        decode_responses=True,
    )
