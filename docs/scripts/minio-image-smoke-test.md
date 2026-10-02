# Test the MinIO image adapter

Run these commands from the repository root with Python dependencies installed from `requirements.txt`. Docker Desktop (or Docker Engine with Compose) must be running. Copy `.env.example` to a private `.env` and set local values for `MINIO_ENDPOINT`, `MINIO_ACCESS_KEY`, `MINIO_SECRET_KEY`, `MINIO_BUCKET`, and `MINIO_SECURE`. The host Python process uses `MINIO_ENDPOINT=127.0.0.1:9000` in the example configuration.

## Start MinIO and the bucket

```powershell
docker compose up -d --wait minio
docker compose ps minio
python -m server.storage.bootstrap
```

The Compose service is named `minio`. Its health status should be `healthy`; its S3 API is bound to `127.0.0.1:9000`. The existing bootstrap command creates the configured `MINIO_BUCKET` if needed. The adapter assumes that bucket already exists and never changes its access policy. It does not check or create the bucket on each upload.

## Automated integration tests

```powershell
python -m pytest tests/test_minio_image_storage.py -q
```

These tests use the real MinIO service and temporary `test/` object keys. Each test deletes only its own key. If MinIO is unreachable, they skip with a start command; if the configured bucket is missing, they report the bootstrap command.

## Manual image smoke test

```powershell
python scripts/minio_image_smoke_test.py path/to/image.png
```

The script uses the production `MinioImageStorage` adapter to upload exact file bytes under a `captures/<uuid>` key, then independently downloads the object and compares bytes. It prints the returned `image_reference` and pauses. To skip the pause while keeping verification and cleanup, add `--no-pause`.

Open the MinIO Console at **http://127.0.0.1:9001**. Sign in with the local development values of `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY` from your private `.env`. In the object browser, open the bucket named by `MINIO_BUCKET` and locate the printed `image_reference`. Download the object and open it locally for visual inspection. The object has no file extension and is stored as `application/octet-stream`; add the original image extension to the downloaded filename if your viewer needs it.

Press Enter in the script terminal after inspection. The script removes the exact uploaded key and verifies it is absent. Refresh the bucket listing or search for that key in Console to confirm cleanup. The script also attempts cleanup if verification fails or it is interrupted after upload; it exits with an error if upload, byte comparison, deletion, or deletion verification fails. It does not leave the test image by default.

Stop only the MinIO service while keeping development data:

```powershell
docker compose stop minio
```

Avoid `docker compose down -v` during routine testing: it deletes persistent volumes, including unrelated development screenshots.
