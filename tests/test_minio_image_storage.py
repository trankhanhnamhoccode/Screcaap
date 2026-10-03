"""Integration checks against the configured local MinIO service."""

from unittest.mock import Mock
from uuid import uuid4

import pytest
from botocore.exceptions import (
    ClientError,
    ConnectTimeoutError,
    EndpointConnectionError,
    ReadTimeoutError,
)

from server.config import get_settings
from server.storage.s3 import MinioImageStorage, create_s3_client


def test_read_closes_s3_response_body_even_when_read_fails() -> None:
    client = Mock()
    body = Mock()
    body.read.side_effect = OSError("stream interrupted")
    client.get_object.return_value = {"Body": body}
    storage = MinioImageStorage(client, "test-bucket")

    with pytest.raises(OSError, match="stream interrupted"):
        storage.read("test/object")

    client.get_object.assert_called_once_with(Bucket="test-bucket", Key="test/object")
    body.close.assert_called_once_with()


def assert_object_missing(client, bucket: str, key: str) -> None:
    with pytest.raises(ClientError) as caught:
        client.head_object(Bucket=bucket, Key=key)
    assert caught.value.response["ResponseMetadata"]["HTTPStatusCode"] == 404


@pytest.fixture
def minio_storage():
    client = create_s3_client()
    bucket = get_settings().minio_bucket
    try:
        client.head_bucket(Bucket=bucket)
    except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError):
        pytest.skip("MinIO unavailable; start it with 'docker compose up -d --wait minio'")
    except ClientError as exc:
        pytest.fail(
            f"Configured MinIO bucket is unavailable ({exc.response['Error']['Code']}); "
            "run 'python -m server.storage.bootstrap'"
        )

    storage = MinioImageStorage(client, bucket, key_prefix="test/")
    created_keys: list[str] = []
    try:
        yield storage, client, bucket, created_keys
    finally:
        for key in created_keys:
            storage.remove(key)


def test_store_preserves_bytes_and_returns_opaque_key(minio_storage) -> None:
    storage, client, bucket, created_keys = minio_storage
    image_bytes = b"\x89PNG\r\n\x1a\n" + bytes(range(256))

    key = storage.store(image_bytes)
    created_keys.append(key)

    assert key.startswith("test/")
    assert "://" not in key
    assert "." not in key
    response = client.get_object(Bucket=bucket, Key=key)
    try:
        assert response["Body"].read() == image_bytes
    finally:
        response["Body"].close()


def test_store_then_read_returns_exact_bytes(minio_storage) -> None:
    storage, _, _, created_keys = minio_storage
    image_bytes = b"\x00\xff\x89PNG\r\n\x1a\n" + bytes(range(256))
    key = storage.store(image_bytes)
    created_keys.append(key)

    assert storage.read(key) == image_bytes


def test_read_missing_object_surfaces_storage_error(minio_storage) -> None:
    storage, _, _, _ = minio_storage
    with pytest.raises(ClientError) as caught:
        storage.read(f"test/{uuid4().hex}")
    assert caught.value.response["ResponseMetadata"]["HTTPStatusCode"] == 404


def test_remove_deletes_created_object(minio_storage) -> None:
    storage, client, bucket, created_keys = minio_storage
    key = storage.store(b"temporary screenshot")
    created_keys.append(key)
    client.head_object(Bucket=bucket, Key=key)

    storage.remove(key)

    assert_object_missing(client, bucket, key)


def test_remove_missing_object_succeeds(minio_storage) -> None:
    storage, client, bucket, _ = minio_storage
    missing_key = f"test/{uuid4().hex}"
    assert_object_missing(client, bucket, missing_key)

    storage.remove(missing_key)

    assert_object_missing(client, bucket, missing_key)
