"""HTTP capture intake validation and service error mapping."""

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from server.api.dependencies import get_capture_service
from server.domain.enums import ProcessingStatus
from server.main import app
from server.services.capture_service import CaptureEnqueueError, DeviceNotFoundError


@pytest.fixture
def client_and_service():
    service = Mock()
    app.dependency_overrides[get_capture_service] = lambda: service
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()


def upload(client: TestClient, image_bytes: bytes, **fields: str):
    data = {
        "device_id": str(uuid4()),
        "captured_at": "2026-10-03T01:23:45+07:00",
        **fields,
    }
    return client.post(
        "/v1/captures",
        data=data,
        files={"image": ("screen.png", image_bytes, "image/png")},
    )


def test_intake_returns_persisted_metadata(client_and_service) -> None:
    client, service = client_and_service
    now = datetime.now(timezone.utc)
    capture_id, device_id = uuid4(), uuid4()
    service.accept_capture.return_value = SimpleNamespace(
        id=capture_id,
        device_id=device_id,
        captured_at=now,
        processing_status=ProcessingStatus.PENDING,
        created_at=now,
        updated_at=now,
    )

    response = upload(client, b"image bytes", device_id=str(device_id))

    assert response.status_code == 202
    assert response.json()["id"] == str(capture_id)
    assert response.json()["processing_status"] == "pending"
    command = service.accept_capture.call_args.args[0]
    assert command.device_id == device_id
    assert command.image_bytes == b"image bytes"
    assert command.captured_at.utcoffset().total_seconds() == 7 * 3600


@pytest.mark.parametrize(
    ("image_bytes", "fields"),
    [
        (b"", {}),
        (b"image", {"captured_at": "2026-10-03T01:23:45"}),
        (b"image", {"captured_at": "not-a-date"}),
        (b"image", {"device_id": "not-a-uuid"}),
    ],
)
def test_invalid_intake_never_calls_service(client_and_service, image_bytes, fields) -> None:
    client, service = client_and_service
    assert upload(client, image_bytes, **fields).status_code == 422
    service.accept_capture.assert_not_called()


def test_unknown_device_is_404(client_and_service) -> None:
    client, service = client_and_service
    service.accept_capture.side_effect = DeviceNotFoundError()
    response = upload(client, b"image")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "device_not_found"


def test_enqueue_failure_returns_committed_capture_id(client_and_service) -> None:
    client, service = client_and_service
    capture_id = uuid4()
    service.accept_capture.side_effect = CaptureEnqueueError(capture_id)
    response = upload(client, b"image")
    assert response.status_code == 503
    assert response.json()["error"]["code"] == "capture_enqueue_failed"
    assert response.json()["error"]["capture_id"] == str(capture_id)


def test_unconfigured_processing_returns_503() -> None:
    with TestClient(app) as client:
        response = upload(client, b"image")
    assert response.status_code == 503
    assert response.json()["detail"]["code"] == "capture_processing_unavailable"


def test_missing_image_is_422(client_and_service) -> None:
    client, service = client_and_service
    response = client.post(
        "/v1/captures",
        data={"device_id": str(uuid4()), "captured_at": "2026-10-02T18:23:45Z"},
    )
    assert response.status_code == 422
    service.accept_capture.assert_not_called()


def test_unexpected_error_does_not_leak_details(client_and_service) -> None:
    client, service = client_and_service
    service.accept_capture.side_effect = RuntimeError("private provider payload")
    response = upload(client, b"image")
    assert response.status_code == 500
    assert "private provider payload" not in response.text
