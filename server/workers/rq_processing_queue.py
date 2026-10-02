"""RQ implementation of the application ProcessingQueue port."""

from uuid import UUID

from rq import Queue


class RqProcessingQueue:
    def __init__(self, queue: Queue, job_target: str) -> None:
        """Receive an importable target path from infrastructure composition."""
        self._queue = queue
        self._job_target = job_target

    def enqueue_capture_processing(self, capture_id: UUID) -> None:
        self._queue.enqueue(self._job_target, str(capture_id))
