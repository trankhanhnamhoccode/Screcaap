"""Small application ports for capture intake."""

from typing import Protocol
from uuid import UUID


class ImageStorage(Protocol):
    def store(self, image_bytes: bytes) -> str: ...

    def remove(self, image_reference: str) -> None: ...


class ProcessingQueue(Protocol):
    def enqueue_capture_processing(self, capture_id: UUID) -> None: ...


class Transaction(Protocol):
    """Commit or roll back the caller-provided database Session."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
