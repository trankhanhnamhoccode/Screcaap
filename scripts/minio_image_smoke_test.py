"""Upload, inspect, and remove one local image through MinioImageStorage."""

import argparse
import sys
from pathlib import Path

from botocore.exceptions import ClientError

# Support `python scripts/minio_image_smoke_test.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.config import get_settings
from server.storage.s3 import create_minio_image_storage, create_s3_client


def object_is_missing(client, bucket: str, key: str) -> bool:
    try:
        client.head_object(Bucket=bucket, Key=key)
    except ClientError as exc:
        if exc.response["ResponseMetadata"]["HTTPStatusCode"] == 404:
            return True
        raise
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image_path", type=Path, help="Local image to upload temporarily")
    parser.add_argument("--no-pause", action="store_true", help="Verify and clean up automatically")
    args = parser.parse_args()

    image_bytes = args.image_path.read_bytes()
    storage = create_minio_image_storage()
    client = create_s3_client()
    bucket = get_settings().minio_bucket
    image_reference: str | None = None

    try:
        image_reference = storage.store(image_bytes)
        print("Uploaded successfully.")
        print(f"image_reference: {image_reference}")

        response = client.get_object(Bucket=bucket, Key=image_reference)
        try:
            downloaded_bytes = response["Body"].read()
        finally:
            response["Body"].close()

        if downloaded_bytes != image_bytes:
            print("Byte round-trip verification: FAIL")
            return 1
        print("Byte round-trip verification: PASS")

        if not args.no_pause:
            print("Open MinIO Console and inspect this object now.")
            input("Press Enter to delete the test object and finish...")
    finally:
        if image_reference is not None:
            print("Deleting test object...")
            storage.remove(image_reference)
            if not object_is_missing(client, bucket, image_reference):
                raise RuntimeError("Deletion verification failed")
            print("Deletion verified.")

    print("Smoke test complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
