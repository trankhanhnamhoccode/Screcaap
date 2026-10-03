"""S3-compatible image storage using the configured MinIO endpoint."""

from uuid import uuid4

import boto3
from botocore.client import BaseClient

from server.config import get_settings


def create_s3_client() -> BaseClient:
    settings = get_settings()
    scheme = "https" if settings.minio_secure else "http"
    return boto3.client(
        "s3",
        endpoint_url=f"{scheme}://{settings.minio_endpoint}",
        aws_access_key_id=settings.minio_access_key,
        aws_secret_access_key=settings.minio_secret_key,
    )


class MinioImageStorage:
    """Store and read screenshot bytes under opaque keys in an existing bucket."""

    def __init__(
        self, client: BaseClient, bucket: str, key_prefix: str = "captures/"
    ) -> None:
        self._client = client
        self._bucket = bucket
        self._key_prefix = key_prefix

    def store(self, image_bytes: bytes) -> str:
        image_reference = f"{self._key_prefix}{uuid4().hex}"
        self._client.put_object(
            Bucket=self._bucket,
            Key=image_reference,
            Body=image_bytes,
            ContentType="application/octet-stream",
        )
        return image_reference

    def read(self, image_reference: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=image_reference)
        body = response["Body"]
        try:
            return body.read()
        finally:
            body.close()

    def remove(self, image_reference: str) -> None:
        # S3 deletion succeeds for an already missing key in an unversioned bucket.
        self._client.delete_object(Bucket=self._bucket, Key=image_reference)


def create_minio_image_storage(*, key_prefix: str = "captures/") -> MinioImageStorage:
    """Wire the adapter to the existing local settings and S3 client."""
    return MinioImageStorage(
        create_s3_client(), get_settings().minio_bucket, key_prefix=key_prefix
    )
