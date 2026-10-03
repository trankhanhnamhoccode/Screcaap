"""Application use case for reading one persisted capture."""

from uuid import UUID

from server.domain.entities import Capture
from server.domain.repositories import CaptureRepository


class CaptureNotFoundError(Exception):
    """No Capture exists for the requested ID."""


class CaptureReadService:
    def __init__(self, capture_repository: CaptureRepository) -> None:
        self._capture_repository = capture_repository

    def get_capture(self, capture_id: UUID) -> Capture:
        capture = self._capture_repository.get_by_id(capture_id)
        if capture is None:
            raise CaptureNotFoundError(f"Capture {capture_id} was not found")
        return capture
