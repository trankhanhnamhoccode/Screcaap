"""Capture HTTP transport schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel

from server.domain.enums import ProcessingStatus


class CaptureUploadRequest(BaseModel):
    device_id: UUID
    captured_at: AwareDatetime


class CaptureAcceptedResponse(BaseModel):
    id: UUID
    device_id: UUID
    captured_at: datetime
    processing_status: ProcessingStatus
    created_at: datetime
    updated_at: datetime


class CaptureErrorDetail(BaseModel):
    code: str
    message: str
    capture_id: UUID | None = None


class CaptureErrorResponse(BaseModel):
    error: CaptureErrorDetail
