"""HTTP contract checks for reading a persisted Capture."""

from datetime import datetime, timezone
from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from server.api.dependencies import get_capture_read_service
from server.domain.entities import Capture
from server.domain.enums import ProcessingStatus
from server.main import app
from server.services.capture_read_service import CaptureNotFoundError


@pytest.fixture
def client_and_service():
    service = Mock()
    app.dependency_overrides[get_capture_read_service] = lambda: service
    try:
        with TestClient(app) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("status", list(ProcessingStatus))
def test_get_returns_persisted_status_and_public_fields(client_and_service, status) -> None:
    client, service = client_and_service
    capture_id, device_id = uuid4(), uuid4()
    observed_at = datetime(2026, 10, 3, 1, 23, 45, tzinfo=timezone.utc)
    service.get_capture.return_value = Capture(
        id=capture_id,
        device_id=device_id,
        captured_at=observed_at,
        processing_status=status,
        created_at=observed_at,
        updated_at=observed_at,
        image_reference="private/image-object-key",
    )

    response = client.get(f"/v1/captures/{capture_id}")

    assert response.status_code == 200
    assert response.json() == {
        "id": str(capture_id),
        "device_id": str(device_id),
        "captured_at": "2026-10-03T01:23:45Z",
        "processing_status": status.value,
        "created_at": "2026-10-03T01:23:45Z",
        "updated_at": "2026-10-03T01:23:45Z",
    }
    assert "image_reference" not in response.text
    assert "image_object_key" not in response.text
    assert "private/image-object-key" not in response.text
    service.get_capture.assert_called_once_with(capture_id)


def test_get_missing_capture_returns_404(client_and_service) -> None:
    client, service = client_and_service
    service.get_capture.side_effect = CaptureNotFoundError()
    response = client.get(f"/v1/captures/{uuid4()}")
    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "capture_not_found", "message": "Capture was not found."}
    }


def test_get_invalid_uuid_uses_transport_validation(client_and_service) -> None:
    client, service = client_and_service
    response = client.get("/v1/captures/not-a-uuid")
    assert response.status_code == 422
    service.get_capture.assert_not_called()
