"""HTTP contract checks for screenshot byte retrieval."""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from server.api.dependencies import get_capture_image_read_service
from server.main import app
from server.services.capture_image_read_service import CaptureImageNotFoundError
from server.services.capture_read_service import CaptureNotFoundError


@pytest.fixture
def client_and_service():
    service = Mock()
    app.dependency_overrides[get_capture_image_read_service] = lambda: service
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            yield client, service
    finally:
        app.dependency_overrides.clear()


def test_image_response_preserves_exact_bytes_and_hides_storage_details(client_and_service) -> None:
    client, service = client_and_service
    capture_id = uuid4()
    stored_bytes = b"\x00\xff\x89PNG\r\n\x1a\n" + bytes(range(256))
    service.get_image.return_value = stored_bytes

    response = client.get(f"/v1/captures/{capture_id}/image")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content == stored_bytes
    assert "image_reference" not in str(response.headers)
    assert "image_object_key" not in str(response.headers)
    assert "bucket" not in str(response.headers).lower()
    assert "minio" not in str(response.headers).lower()
    service.get_image.assert_called_once_with(capture_id)


def test_missing_capture_reuses_not_found_error(client_and_service) -> None:
    client, service = client_and_service
    service.get_image.side_effect = CaptureNotFoundError("private repository detail")

    response = client.get(f"/v1/captures/{uuid4()}/image")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "capture_not_found", "message": "Capture was not found."}
    }


def test_capture_without_image_reference_has_distinct_404(client_and_service) -> None:
    client, service = client_and_service
    service.get_image.side_effect = CaptureImageNotFoundError("private reference")

    response = client.get(f"/v1/captures/{uuid4()}/image")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "capture_image_not_found", "message": "Capture image was not found."}
    }


def test_invalid_capture_id_uses_fastapi_validation(client_and_service) -> None:
    client, service = client_and_service
    response = client.get("/v1/captures/invalid/image")
    assert response.status_code == 422
    service.get_image.assert_not_called()


def test_storage_failure_does_not_leak_provider_details(client_and_service) -> None:
    client, service = client_and_service
    service.get_image.side_effect = RuntimeError(
        "MinIO bucket=private key=captures/secret endpoint=example credentials=secret"
    )

    response = client.get(f"/v1/captures/{uuid4()}/image")

    assert response.status_code == 500
    assert response.text == "Internal Server Error"
