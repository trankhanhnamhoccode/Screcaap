"""Small application ports for capture intake and processing."""

from typing import Protocol
from uuid import UUID


class CaptureProcessor(Protocol):
    """Perform opaque processing for a capture after its claim is committed."""

    def process(self, capture_id: UUID) -> None: ...


class ImageStorage(Protocol):
    def store(self, image_bytes: bytes) -> str: ...

    def read(self, image_reference: str) -> bytes: ...

    def remove(self, image_reference: str) -> None: ...


class ProcessingQueue(Protocol):
    def enqueue_capture_processing(self, capture_id: UUID) -> None: ...


class Transaction(Protocol):
    """Commit or roll back the caller-provided database Session."""

    def commit(self) -> None: ...

    def rollback(self) -> None: ...
