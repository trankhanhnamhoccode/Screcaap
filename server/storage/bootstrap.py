"""Create the configured local development bucket if it is absent."""

from server.config import get_settings
from server.storage.s3 import create_s3_client


def main() -> None:
    bucket = get_settings().minio_bucket
    client = create_s3_client()
    existing = {item["Name"] for item in client.list_buckets()["Buckets"]}
    if bucket not in existing:
        client.create_bucket(Bucket=bucket)
    print(f"MinIO bucket ready: {bucket}")


if __name__ == "__main__":
    main()
