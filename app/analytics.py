import asyncio
import logging
import os

import redis
from sqlalchemy import update

from app.cache import redis_client
from app.database import SessionLocal
from app.models import Url

logger = logging.getLogger("analytics")

FLUSH_INTERVAL_SECONDS = int(os.environ.get("CLICK_FLUSH_SECONDS", "10"))


def _key(short_code: str) -> str:
    return f"clicks:{short_code}"


def record_click(short_code: str) -> None:
    """Add one tally mark. Runs after the redirect reply is sent."""
    try:
        redis_client.incr(_key(short_code))
    except redis.RedisError:
        logger.warning("Redis unavailable, click not counted")


def get_pending_clicks(short_code: str) -> int:
    """Tally marks that are still waiting in Redis."""
    try:
        return int(redis_client.get(_key(short_code)) or 0)
    except redis.RedisError:
        return 0


def flush_clicks() -> int:
    """Copy tallies from Redis into Postgres. Returns how many links were updated."""
    updated = 0
    try:
        for key in list(redis_client.scan_iter(match="clicks:*")):
            count = redis_client.getdel(key)  # read and clear in one step
            if count is None:
                continue
            short_code = key.split(":", 1)[1]
            try:
                with SessionLocal() as db:
                    db.execute(
                        update(Url)
                        .where(Url.short_code == short_code)
                        .values(click_count=Url.click_count + int(count))
                    )
                    db.commit()
                updated += 1
            except Exception:
                redis_client.incrby(key, int(count))  # put the tally back
                raise
    except redis.RedisError:
        logger.warning("Redis unavailable, click flush skipped")
    return updated


async def flush_loop() -> None:
    """Every few seconds, copy the tallies into Postgres."""
    while True:
        await asyncio.sleep(FLUSH_INTERVAL_SECONDS)
        try:
            await asyncio.to_thread(flush_clicks)
        except Exception:
            logger.exception("Click flush failed, will retry")