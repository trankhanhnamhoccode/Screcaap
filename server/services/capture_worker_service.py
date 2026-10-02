"""Transaction-safe orchestration of one capture processing attempt."""

from contextlib import suppress
from uuid import UUID

from server.domain.enums import ProcessingStatus
from server.domain.repositories import CaptureRepository
from server.services.ports import CaptureProcessor, Transaction


class CaptureNotFoundError(Exception):
    """The queued capture no longer exists."""


class CaptureClaimError(Exception):
    """A pending capture could not be claimed."""


class CaptureStateTransitionError(Exception):
    """A claimed capture could not be put in its final state."""


class CaptureWorkerService:
    def __init__(
        self,
        capture_repository: CaptureRepository,
        processor: CaptureProcessor,
        transaction: Transaction,
    ) -> None:
        self._captures = capture_repository
        self._processor = processor
        self._transaction = transaction

    def process_capture(self, capture_id: UUID) -> None:
        try:
            claimed = self._captures.claim_for_processing(capture_id)
            if not claimed:
                capture = self._captures.get_by_id(capture_id)
                if capture is None:
                    raise CaptureNotFoundError(f"Capture {capture_id} was not found")
                if capture.processing_status == ProcessingStatus.PENDING:
                    raise CaptureClaimError(f"Pending capture {capture_id} was not claimed")
                self._transaction.rollback()
                return
            self._transaction.commit()
        except Exception:
            with suppress(Exception):
                self._transaction.rollback()
            raise

        try:
            self._processor.process(capture_id)
        except Exception as processing_error:
            try:
                self._persist_final_state(capture_id, completed=False)
            except Exception as persistence_error:
                raise processing_error from persistence_error
            raise

        self._persist_final_state(capture_id, completed=True)

    def _persist_final_state(self, capture_id: UUID, *, completed: bool) -> None:
        try:
            if completed:
                changed = self._captures.complete_processing(capture_id)
            else:
                changed = self._captures.fail_processing(capture_id)
            if not changed:
                target = "completed" if completed else "failed"
                raise CaptureStateTransitionError(
                    f"Capture {capture_id} could not transition from processing to {target}"
                )
            self._transaction.commit()
        except Exception:
            with suppress(Exception):
                self._transaction.rollback()
            raise
