"""OCR result persistence through an externally managed Session."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from server.database.models import OCRResultModel
from server.domain.entities import OCRResult


class SqlAlchemyOCRResultRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, result: OCRResult) -> None:
        self._session.add(
            OCRResultModel(
                id=result.id,
                capture_id=result.capture_id,
                text=result.text,
                created_at=result.created_at,
                updated_at=result.updated_at,
            )
        )

    def get_by_capture_id(self, capture_id: UUID) -> OCRResult | None:
        model = self._session.scalars(
            select(OCRResultModel).where(OCRResultModel.capture_id == capture_id)
        ).one_or_none()
        if model is None:
            return None
        return OCRResult(
            id=model.id,
            capture_id=model.capture_id,
            text=model.text,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
