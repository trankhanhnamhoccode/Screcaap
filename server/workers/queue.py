"""RQ connection setup; application services will use a queue abstraction."""

from redis import Redis
from rq import Queue

from server.config import get_settings


def create_redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def create_queue(connection: Redis | None = None) -> Queue:
    return Queue("default", connection=connection or create_redis_connection())
