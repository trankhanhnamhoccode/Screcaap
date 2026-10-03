"""Capture persistence through an externally managed Session."""

from uuid import UUID

from sqlalchemy import func, update
from sqlalchemy.orm import Session

from server.database.models import CaptureModel
from server.domain.entities import Capture
from server.domain.enums import ProcessingStatus


class SqlAlchemyCaptureRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, capture: Capture) -> None:
        self._session.add(
            CaptureModel(
                id=capture.id,
                device_id=capture.device_id,
                captured_at=capture.captured_at,
                processing_status=capture.processing_status.value,
                image_object_key=capture.image_reference,
                created_at=capture.created_at,
                updated_at=capture.updated_at,
            )
        )

    def get_by_id(self, capture_id: UUID) -> Capture | None:
        model = self._session.get(CaptureModel, capture_id)
        if model is None:
            return None
        return Capture(
            id=model.id,
            device_id=model.device_id,
            captured_at=model.captured_at,
            processing_status=ProcessingStatus(model.processing_status),
            created_at=model.created_at,
            updated_at=model.updated_at,
            image_reference=model.image_object_key,
        )

    def claim_for_processing(self, capture_id: UUID) -> bool:
        return self._transition(capture_id, ProcessingStatus.PENDING, ProcessingStatus.PROCESSING)

    def complete_processing(self, capture_id: UUID) -> bool:
        return self._transition(capture_id, ProcessingStatus.PROCESSING, ProcessingStatus.COMPLETED)

    def fail_processing(self, capture_id: UUID) -> bool:
        return self._transition(capture_id, ProcessingStatus.PROCESSING, ProcessingStatus.FAILED)

    def _transition(
        self, capture_id: UUID, from_status: ProcessingStatus, to_status: ProcessingStatus
    ) -> bool:
        result = self._session.execute(
            update(CaptureModel)
            .where(CaptureModel.id == capture_id)
            .where(CaptureModel.processing_status == from_status.value)
            .values(processing_status=to_status.value, updated_at=func.now())
        )
        return result.rowcount == 1
