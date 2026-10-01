"""S3-compatible client setup for the future ImageStorage adapter."""

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
