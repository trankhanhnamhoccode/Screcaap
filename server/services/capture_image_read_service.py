"""Application use case for reading a Capture's stored screenshot."""

from uuid import UUID

from server.domain.repositories import CaptureRepository
from server.services.capture_read_service import CaptureNotFoundError
from server.services.ports import ImageStorage


class CaptureImageNotFoundError(Exception):
    """The Capture has no image reference."""


class CaptureImageReadService:
    def __init__(
        self, capture_repository: CaptureRepository, image_storage: ImageStorage
    ) -> None:
        self._capture_repository = capture_repository
        self._image_storage = image_storage

    def get_image(self, capture_id: UUID) -> bytes:
        capture = self._capture_repository.get_by_id(capture_id)
        if capture is None:
            raise CaptureNotFoundError(f"Capture {capture_id} was not found")
        if capture.image_reference is None:
            raise CaptureImageNotFoundError(f"Capture {capture_id} has no image")
        return self._image_storage.read(capture.image_reference)
