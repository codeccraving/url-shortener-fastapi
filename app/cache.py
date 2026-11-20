import logging
import os

import redis

logger = logging.getLogger("cache")

REDIS_URL = os.environ["REDIS_URL"]
CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "3600"))

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def _key(short_code: str) -> str:
    return f"url:{short_code}"


def get_cached_url(short_code: str) -> str | None:
    try:
        return redis_client.get(_key(short_code))
    except redis.RedisError:
        logger.warning("Redis unavailable, falling back to the database")
        return None


def set_cached_url(short_code: str, long_url: str) -> None:
    try:
        redis_client.set(_key(short_code), long_url, ex=CACHE_TTL_SECONDS)
    except redis.RedisError:
        logger.warning("Redis unavailable, skipping cache write")