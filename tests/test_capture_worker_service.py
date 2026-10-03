"""Capture worker orchestration without provider or queue dependencies."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest

from server.domain.entities import Capture
from server.domain.enums import ProcessingStatus
from server.domain.repositories import CaptureRepository
from server.services.capture_worker_service import (
    CaptureClaimError,
    CaptureNotFoundError,
    CaptureStateTransitionError,
    CaptureWorkerService,
)
from server.services.ports import CaptureProcessor, Transaction


@pytest.fixture
def worker():
    capture_id = uuid4()
    repository = Mock(spec=CaptureRepository)
    repository.claim_for_processing.return_value = True
    repository.complete_processing.return_value = True
    repository.fail_processing.return_value = True
    processor = Mock(spec=CaptureProcessor)
    transaction = Mock(spec=Transaction)
    service = CaptureWorkerService(repository, processor, transaction)
    return SimpleNamespace(
        capture_id=capture_id, repository=repository, processor=processor,
        transaction=transaction, service=service,
    )


def capture_in_state(capture_id, status):
    now = datetime.now(timezone.utc)
    return Capture(
        id=capture_id, device_id=uuid4(), captured_at=now,
        processing_status=status, created_at=now, updated_at=now,
    )


def test_success_commits_claim_before_processor_and_completion_after(worker) -> None:
    events = []
    worker.repository.claim_for_processing.side_effect = lambda _: events.append("claim") or True
    worker.transaction.commit.side_effect = lambda: events.append("commit")
    worker.processor.process.side_effect = lambda _: events.append("processor")
    worker.repository.complete_processing.side_effect = lambda _: events.append("complete") or True

    worker.service.process_capture(worker.capture_id)

    assert events == ["claim", "commit", "processor", "complete", "commit"]
    worker.processor.process.assert_called_once_with(worker.capture_id)
    worker.transaction.rollback.assert_not_called()


@pytest.mark.parametrize(
    "status", [ProcessingStatus.PROCESSING, ProcessingStatus.COMPLETED, ProcessingStatus.FAILED]
)
def test_duplicate_or_failed_capture_skips_processing(worker, status) -> None:
    worker.repository.claim_for_processing.return_value = False
    worker.repository.get_by_id.return_value = capture_in_state(worker.capture_id, status)

    worker.service.process_capture(worker.capture_id)

    worker.processor.process.assert_not_called()
    worker.repository.complete_processing.assert_not_called()
    worker.repository.fail_processing.assert_not_called()
    worker.transaction.commit.assert_not_called()
    worker.transaction.rollback.assert_called_once_with()


def test_missing_capture_is_error(worker) -> None:
    worker.repository.claim_for_processing.return_value = False
    worker.repository.get_by_id.return_value = None

    with pytest.raises(CaptureNotFoundError, match=str(worker.capture_id)):
        worker.service.process_capture(worker.capture_id)

    worker.processor.process.assert_not_called()
    worker.transaction.rollback.assert_called_once_with()


def test_unclaimed_pending_capture_is_error(worker) -> None:
    worker.repository.claim_for_processing.return_value = False
    worker.repository.get_by_id.return_value = capture_in_state(
        worker.capture_id, ProcessingStatus.PENDING
    )

    with pytest.raises(CaptureClaimError):
        worker.service.process_capture(worker.capture_id)

    worker.processor.process.assert_not_called()


def test_claim_commit_failure_rolls_back_without_processing(worker) -> None:
    failure = RuntimeError("claim commit failed")
    events = []
    worker.repository.claim_for_processing.side_effect = lambda _: events.append("claim") or True

    def fail_commit():
        events.append("commit")
        raise failure

    worker.transaction.commit.side_effect = fail_commit
    worker.transaction.rollback.side_effect = lambda: events.append("rollback")

    with pytest.raises(RuntimeError) as caught:
        worker.service.process_capture(worker.capture_id)

    assert caught.value is failure
    assert events == ["claim", "commit", "rollback"]
    worker.processor.process.assert_not_called()


def test_processor_failure_persists_failed_and_surfaces_original(worker) -> None:
    failure = RuntimeError("processor failed")
    events = []
    worker.repository.claim_for_processing.side_effect = lambda _: events.append("claim") or True
    worker.transaction.commit.side_effect = lambda: events.append("commit")

    def fail_processing(_):
        events.append("processor")
        raise failure

    worker.processor.process.side_effect = fail_processing
    worker.repository.fail_processing.side_effect = lambda _: events.append("fail") or True

    with pytest.raises(RuntimeError) as caught:
        worker.service.process_capture(worker.capture_id)

    assert caught.value is failure
    assert events == ["claim", "commit", "processor", "fail", "commit"]
    worker.repository.complete_processing.assert_not_called()


def test_failure_state_persistence_error_preserves_both_errors(worker) -> None:
    processing_error = RuntimeError("processor failed")
    persistence_error = RuntimeError("failed state commit failed")
    worker.processor.process.side_effect = processing_error
    worker.transaction.commit.side_effect = [None, persistence_error]

    with pytest.raises(RuntimeError) as caught:
        worker.service.process_capture(worker.capture_id)

    assert caught.value is processing_error
    assert caught.value.__cause__ is persistence_error
    worker.transaction.rollback.assert_called_once_with()


@pytest.mark.parametrize("transition_result", [False, RuntimeError("completion update failed")])
def test_completion_transition_failure_is_surfaced(worker, transition_result) -> None:
    if isinstance(transition_result, Exception):
        worker.repository.complete_processing.side_effect = transition_result
    else:
        worker.repository.complete_processing.return_value = transition_result

    with pytest.raises((CaptureStateTransitionError, RuntimeError)):
        worker.service.process_capture(worker.capture_id)

    worker.processor.process.assert_called_once_with(worker.capture_id)
    assert worker.transaction.commit.call_count == 1
    worker.transaction.rollback.assert_called_once_with()


def test_completion_commit_failure_is_surfaced(worker) -> None:
    failure = RuntimeError("completion commit failed")
    worker.transaction.commit.side_effect = [None, failure]

    with pytest.raises(RuntimeError) as caught:
        worker.service.process_capture(worker.capture_id)

    assert caught.value is failure
    worker.processor.process.assert_called_once_with(worker.capture_id)
    worker.transaction.rollback.assert_called_once_with()
