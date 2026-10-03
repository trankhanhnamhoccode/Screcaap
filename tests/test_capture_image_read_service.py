"""Capture image read use case with repository and storage fakes."""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest

from server.domain.entities import Capture
from server.domain.enums import ProcessingStatus
from server.domain.repositories import CaptureRepository
from server.services.capture_image_read_service import (
    CaptureImageNotFoundError,
    CaptureImageReadService,
)
from server.services.capture_read_service import CaptureNotFoundError
from server.services.ports import ImageStorage


def make_capture(image_reference: str | None) -> Capture:
    now = datetime.now(timezone.utc)
    return Capture(
        id=uuid4(),
        device_id=uuid4(),
        captured_at=now,
        processing_status=ProcessingStatus.PENDING,
        created_at=now,
        updated_at=now,
        image_reference=image_reference,
    )


def test_get_image_reads_exact_bytes_from_opaque_reference() -> None:
    captures = Mock(spec=CaptureRepository)
    storage = Mock(spec=ImageStorage)
    capture = make_capture("captures/opaque-key")
    captures.get_by_id.return_value = capture
    stored_bytes = b"\x00\xff\x10screen\x00\x80"
    storage.read.return_value = stored_bytes

    result = CaptureImageReadService(captures, storage).get_image(capture.id)

    assert result == stored_bytes
    captures.get_by_id.assert_called_once_with(capture.id)
    storage.read.assert_called_once_with("captures/opaque-key")


def test_missing_capture_does_not_read_storage() -> None:
    captures = Mock(spec=CaptureRepository)
    storage = Mock(spec=ImageStorage)
    captures.get_by_id.return_value = None
    capture_id = uuid4()

    with pytest.raises(CaptureNotFoundError):
        CaptureImageReadService(captures, storage).get_image(capture_id)

    storage.read.assert_not_called()


def test_capture_without_image_reference_does_not_read_storage() -> None:
    captures = Mock(spec=CaptureRepository)
    storage = Mock(spec=ImageStorage)
    capture = make_capture(None)
    captures.get_by_id.return_value = capture

    with pytest.raises(CaptureImageNotFoundError):
        CaptureImageReadService(captures, storage).get_image(capture.id)

    storage.read.assert_not_called()
