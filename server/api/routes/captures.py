"""HTTP intake for timestamped screenshot captures."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from pydantic import AwareDatetime

from server.api.dependencies import get_capture_service
from server.services.capture_service import (
    CaptureEnqueueError,
    CaptureIntakeCommand,
    CaptureService,
    DeviceNotFoundError,
)
from shared.schemas.capture import (
    CaptureAcceptedResponse,
    CaptureErrorDetail,
    CaptureErrorResponse,
    CaptureUploadRequest,
)

router = APIRouter(prefix="/v1/captures", tags=["captures"])


@router.post(
    "",
    status_code=202,
    response_model=CaptureAcceptedResponse,
    responses={404: {"model": CaptureErrorResponse}, 503: {"model": CaptureErrorResponse}},
)
def create_capture(
    device_id: UUID = Form(...),
    captured_at: AwareDatetime = Form(...),
    image: UploadFile = File(...),
    service: CaptureService = Depends(get_capture_service),
) -> CaptureAcceptedResponse | JSONResponse:
    metadata = CaptureUploadRequest(device_id=device_id, captured_at=captured_at)

    image_bytes = image.file.read()
    if not image_bytes:
        return _error_response(422, "empty_image", "Image must not be empty.")

    try:
        capture = service.accept_capture(
            CaptureIntakeCommand(
                device_id=metadata.device_id,
                captured_at=metadata.captured_at,
                image_bytes=image_bytes,
            )
        )
    except DeviceNotFoundError:
        return _error_response(404, "device_not_found", "Device was not found.")
    except CaptureEnqueueError as exc:
        return _error_response(
            503,
            "capture_enqueue_failed",
            "Capture was stored but background processing could not be scheduled.",
            capture_id=exc.capture_id,
        )

    return CaptureAcceptedResponse(
        id=capture.id,
        device_id=capture.device_id,
        captured_at=capture.captured_at,
        processing_status=capture.processing_status,
        created_at=capture.created_at,
        updated_at=capture.updated_at,
    )


def _error_response(
    status_code: int, code: str, message: str, *, capture_id: UUID | None = None
) -> JSONResponse:
    body = CaptureErrorResponse(
        error=CaptureErrorDetail(code=code, message=message, capture_id=capture_id)
    )
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json", exclude_none=True))
