"""Application use case for accepting a screenshot capture."""

from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID, uuid4

from server.domain.entities import Capture
from server.domain.enums import ProcessingStatus
from server.domain.repositories import CaptureRepository, DeviceRepository
from server.services.ports import ImageStorage, ProcessingQueue, Transaction


@dataclass(frozen=True)
class CaptureIntakeCommand:
    device_id: UUID
    captured_at: datetime
    image_bytes: bytes

    def __post_init__(self) -> None:
        if self.captured_at.tzinfo is None or self.captured_at.utcoffset() is None:
            raise ValueError("captured_at must be timezone-aware")


class DeviceNotFoundError(Exception):
    """The requested device does not exist."""


class CaptureEnqueueError(Exception):
    """The capture was committed, but scheduling its processing failed."""

    def __init__(self, capture_id: UUID) -> None:
        self.capture_id = capture_id
        super().__init__(f"Capture {capture_id} was committed but not enqueued")


class CaptureService:
    def __init__(
        self,
        device_repository: DeviceRepository,
        capture_repository: CaptureRepository,
        image_storage: ImageStorage,
        processing_queue: ProcessingQueue,
        transaction: Transaction,
    ) -> None:
        self._device_repository = device_repository
        self._capture_repository = capture_repository
        self._image_storage = image_storage
        self._processing_queue = processing_queue
        self._transaction = transaction

    def accept_capture(self, command: CaptureIntakeCommand) -> Capture:
        image_reference: str | None = None
        try:
            if self._device_repository.get_by_id(command.device_id) is None:
                raise DeviceNotFoundError(f"Device {command.device_id} was not found")

            capture_id = uuid4()
            image_reference = self._image_storage.store(command.image_bytes)
            now = datetime.now(timezone.utc)
            capture = Capture(
                id=capture_id,
                device_id=command.device_id,
                captured_at=command.captured_at,
                processing_status=ProcessingStatus.PENDING,
                created_at=now,
                updated_at=now,
                image_reference=image_reference,
            )
            self._capture_repository.add(capture)
            self._transaction.commit()
        except Exception:
            with suppress(Exception):
                self._transaction.rollback()
            if image_reference is not None:
                with suppress(Exception):
                    self._image_storage.remove(image_reference)
            raise

        try:
            self._processing_queue.enqueue_capture_processing(capture.id)
        except Exception as exc:
            raise CaptureEnqueueError(capture.id) from exc
        return capture
