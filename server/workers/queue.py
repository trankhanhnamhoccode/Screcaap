"""Redis connection and RQ queue construction."""

from redis import Redis
from rq import Queue

from server.config import get_settings

CAPTURE_PROCESSING_QUEUE_NAME = "capture-processing"


def create_redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url)


def create_queue(connection: Redis | None = None) -> Queue:
    return Queue("default", connection=connection or create_redis_connection())


def create_capture_processing_queue(connection: Redis | None = None) -> Queue:
    return Queue(
        CAPTURE_PROCESSING_QUEUE_NAME,
        connection=connection or create_redis_connection(),
    )
