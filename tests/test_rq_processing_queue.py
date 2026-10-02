"""Integration checks for the RQ adapter against local Redis."""

from uuid import uuid4

import pytest
from redis.exceptions import ConnectionError, TimeoutError
from rq.job import Job

from server.workers.queue import (
    CAPTURE_PROCESSING_QUEUE_NAME,
    create_capture_processing_queue,
    create_redis_connection,
)
from server.workers.rq_processing_queue import RqProcessingQueue

SMOKE_JOB_TARGET = "scripts.rq_smoke_job.echo_capture_id"


@pytest.fixture
def rq_adapter():
    connection = create_redis_connection()
    try:
        connection.ping()
    except (ConnectionError, TimeoutError):
        pytest.skip("Redis unavailable; start it with 'docker compose up -d --wait redis'")

    queue = create_capture_processing_queue(connection)
    adapter = RqProcessingQueue(queue, SMOKE_JOB_TARGET)
    created_job_ids: list[str] = []
    try:
        yield adapter, queue, connection, created_job_ids
    finally:
        for job_id in created_job_ids:
            Job.fetch(job_id, connection=connection).delete(remove_from_queue=True)
            assert job_id not in queue.get_job_ids()


def enqueue_and_track(adapter, queue, created_job_ids: list[str], capture_id) -> str:
    before = set(queue.get_job_ids())
    assert adapter.enqueue_capture_processing(capture_id) is None
    new_job_ids = set(queue.get_job_ids()) - before
    created_job_ids.extend(new_job_ids)
    assert len(new_job_ids) == 1
    return new_job_ids.pop()


def test_enqueue_creates_real_rq_job_with_only_capture_id(rq_adapter) -> None:
    adapter, queue, connection, created_job_ids = rq_adapter
    capture_id = uuid4()

    job_id = enqueue_and_track(adapter, queue, created_job_ids, capture_id)
    job = Job.fetch(job_id, connection=connection)

    assert queue.name == CAPTURE_PROCESSING_QUEUE_NAME
    assert job.origin == CAPTURE_PROCESSING_QUEUE_NAME
    assert job_id in queue.get_job_ids()
    assert job.func_name == SMOKE_JOB_TARGET
    assert job.args == (str(capture_id),)
    assert job.kwargs == {}


def test_repeated_enqueue_creates_distinct_jobs(rq_adapter) -> None:
    adapter, queue, connection, created_job_ids = rq_adapter
    capture_id = uuid4()

    first_id = enqueue_and_track(adapter, queue, created_job_ids, capture_id)
    second_id = enqueue_and_track(adapter, queue, created_job_ids, capture_id)

    assert first_id != second_id
    assert Job.fetch(first_id, connection=connection).args == (str(capture_id),)
    assert Job.fetch(second_id, connection=connection).args == (str(capture_id),)
