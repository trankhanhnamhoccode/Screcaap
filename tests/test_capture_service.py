"""Capture intake orchestration with domain and application fakes."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from server.domain.entities import Capture, Device
from server.domain.enums import ProcessingStatus
from server.domain.repositories import CaptureRepository, DeviceRepository
from server.services.capture_service import (
    CaptureEnqueueError,
    CaptureIntakeCommand,
    CaptureService,
    DeviceNotFoundError,
)
from server.services.ports import ImageStorage, ProcessingQueue, Transaction


@pytest.fixture
def intake():
    device_id = uuid4()
    device_repository = Mock(spec=DeviceRepository)
    device_repository.get_by_id.return_value = Device(
        id=device_id, user_id=uuid4(), name="Laptop", created_at=datetime.now(timezone.utc)
    )
    capture_repository = Mock(spec=CaptureRepository)
    image_storage = Mock(spec=ImageStorage)
    image_storage.store.return_value = "captures/example.png"
    processing_queue = Mock(spec=ProcessingQueue)
    transaction = Mock(spec=Transaction)
    service = CaptureService(
        device_repository, capture_repository, image_storage, processing_queue, transaction
    )
    command = CaptureIntakeCommand(
        device_id=device_id,
        captured_at=datetime(2026, 10, 1, 8, 30, tzinfo=timezone.utc),
        image_bytes=b"screenshot bytes",
    )
    return SimpleNamespace(
        service=service,
        command=command,
        device_repository=device_repository,
        capture_repository=capture_repository,
        image_storage=image_storage,
        processing_queue=processing_queue,
        transaction=transaction,
    )


def test_accept_capture_persists_pending_domain_capture_then_enqueues(intake) -> None:
    events = []

    def store(image_bytes: bytes) -> str:
        events.append("store")
        return "captures/example.png"

    intake.image_storage.store.side_effect = store
    intake.capture_repository.add.side_effect = lambda capture: events.append("add")
    intake.transaction.commit.side_effect = lambda: events.append("commit")
    intake.processing_queue.enqueue_capture_processing.side_effect = (
        lambda capture_id: events.append("enqueue")
    )

    capture = intake.service.accept_capture(intake.command)

    assert events == ["store", "add", "commit", "enqueue"]
    assert type(capture) is Capture
    assert capture.id is not None
    assert capture.device_id == intake.command.device_id
    assert capture.captured_at == intake.command.captured_at
    assert capture.processing_status is ProcessingStatus.PENDING
    assert capture.image_reference == "captures/example.png"
    assert capture.created_at == capture.updated_at
    assert capture.created_at.tzinfo is not None
    intake.device_repository.get_by_id.assert_called_once_with(intake.command.device_id)
    intake.image_storage.store.assert_called_once_with(intake.command.image_bytes)
    intake.capture_repository.add.assert_called_once_with(capture)
    intake.processing_queue.enqueue_capture_processing.assert_called_once_with(capture.id)
    intake.transaction.rollback.assert_not_called()


def test_missing_device_has_no_storage_capture_or_job(intake) -> None:
    intake.device_repository.get_by_id.return_value = None

    with pytest.raises(DeviceNotFoundError):
        intake.service.accept_capture(intake.command)

    intake.image_storage.store.assert_not_called()
    intake.capture_repository.add.assert_not_called()
    intake.processing_queue.enqueue_capture_processing.assert_not_called()
    intake.transaction.commit.assert_not_called()
    intake.transaction.rollback.assert_called_once_with()


def test_storage_failure_prevents_capture_and_job(intake) -> None:
    failure = RuntimeError("storage unavailable")
    intake.image_storage.store.side_effect = failure

    with pytest.raises(RuntimeError) as caught:
        intake.service.accept_capture(intake.command)

    assert caught.value is failure
    intake.capture_repository.add.assert_not_called()
    intake.processing_queue.enqueue_capture_processing.assert_not_called()
    intake.transaction.commit.assert_not_called()
    intake.transaction.rollback.assert_called_once_with()
    intake.image_storage.remove.assert_not_called()


def test_commit_failure_rolls_back_and_removes_image(intake) -> None:
    failure = RuntimeError("database commit failed")
    intake.transaction.commit.side_effect = failure

    with pytest.raises(RuntimeError) as caught:
        intake.service.accept_capture(intake.command)

    assert caught.value is failure
    intake.capture_repository.add.assert_called_once()
    intake.transaction.rollback.assert_called_once_with()
    intake.image_storage.remove.assert_called_once_with("captures/example.png")
    intake.processing_queue.enqueue_capture_processing.assert_not_called()


def test_repository_add_failure_rolls_back_and_removes_image(intake) -> None:
    failure = RuntimeError("database insert failed")
    intake.capture_repository.add.side_effect = failure

    with pytest.raises(RuntimeError) as caught:
        intake.service.accept_capture(intake.command)

    assert caught.value is failure
    intake.transaction.rollback.assert_called_once_with()
    intake.image_storage.remove.assert_called_once_with("captures/example.png")
    intake.transaction.commit.assert_not_called()
    intake.processing_queue.enqueue_capture_processing.assert_not_called()


def test_cleanup_failure_does_not_hide_commit_failure(intake) -> None:
    failure = RuntimeError("database commit failed")
    intake.transaction.commit.side_effect = failure
    intake.image_storage.remove.side_effect = RuntimeError("cleanup failed")

    with pytest.raises(RuntimeError) as caught:
        intake.service.accept_capture(intake.command)

    assert caught.value is failure
    intake.transaction.rollback.assert_called_once_with()
    intake.image_storage.remove.assert_called_once_with("captures/example.png")


def test_enqueue_failure_surfaces_committed_capture_id_without_cleanup(intake) -> None:
    failure = RuntimeError("queue unavailable")
    intake.processing_queue.enqueue_capture_processing.side_effect = failure

    with pytest.raises(CaptureEnqueueError) as caught:
        intake.service.accept_capture(intake.command)

    capture = intake.capture_repository.add.call_args.args[0]
    assert caught.value.capture_id == capture.id
    assert caught.value.__cause__ is failure
    assert capture.processing_status is ProcessingStatus.PENDING
    intake.transaction.commit.assert_called_once_with()
    intake.transaction.rollback.assert_not_called()
    intake.image_storage.remove.assert_not_called()


def test_invalid_capture_time_is_rejected_before_side_effects(intake) -> None:
    with pytest.raises(ValueError, match="captured_at must be timezone-aware"):
        CaptureIntakeCommand(
            device_id=intake.command.device_id,
            captured_at=datetime(2026, 10, 1, 8, 30),
            image_bytes=intake.command.image_bytes,
        )

    intake.image_storage.store.assert_not_called()
    intake.capture_repository.add.assert_not_called()
