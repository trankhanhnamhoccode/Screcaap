"""HTTP intake for timestamped screenshot captures."""

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import AwareDatetime

from server.api.dependencies import (
    get_capture_image_read_service,
    get_capture_read_service,
    get_capture_service,
)
from server.domain.entities import Capture
from server.services.capture_read_service import CaptureNotFoundError, CaptureReadService
from server.services.capture_image_read_service import (
    CaptureImageNotFoundError,
    CaptureImageReadService,
)
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

    return _capture_response(capture)


@router.get(
    "/{capture_id}",
    response_model=CaptureAcceptedResponse,
    responses={404: {"model": CaptureErrorResponse}},
)
def get_capture(
    capture_id: UUID,
    service: CaptureReadService = Depends(get_capture_read_service),
) -> CaptureAcceptedResponse | JSONResponse:
    try:
        capture = service.get_capture(capture_id)
    except CaptureNotFoundError:
        return _error_response(404, "capture_not_found", "Capture was not found.")
    return _capture_response(capture)


@router.get(
    "/{capture_id}/image",
    response_class=Response,
    responses={
        200: {
            "content": {
                "application/octet-stream": {
                    "schema": {"type": "string", "format": "binary"}
                }
            }
        },
        404: {"model": CaptureErrorResponse},
    },
)
def get_capture_image(
    capture_id: UUID,
    service: CaptureImageReadService = Depends(get_capture_image_read_service),
) -> Response:
    try:
        image_bytes = service.get_image(capture_id)
    except CaptureNotFoundError:
        return _error_response(404, "capture_not_found", "Capture was not found.")
    except CaptureImageNotFoundError:
        return _error_response(404, "capture_image_not_found", "Capture image was not found.")
    return Response(content=image_bytes, media_type="application/octet-stream")


def _capture_response(capture: Capture) -> CaptureAcceptedResponse:
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
