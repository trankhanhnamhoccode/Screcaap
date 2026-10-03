# Local backend development

## Prerequisites

Install Python 3.11 or newer and Docker Desktop (or Docker Engine with the Compose plugin). PostgreSQL, Redis, and MinIO run in Docker; do not install those services separately on the host. Run the commands below from the repository root. The API and RQ worker run in a host Python virtual environment.

This includes the `POST /v1/captures` HTTP intake route, `GET /v1/captures/{capture_id}` read route, their application services, the MinIO image adapter, and the RQ queue adapter. Production capture processing, OCR, analysis, and timeline routes are not implemented. POST uses multipart fields `image`, `device_id`, and `captured_at`; its default processing-queue dependency returns `503` until a real processor and RQ job target can be composed. GET uses PostgreSQL only and can be tested without MinIO or Redis. Authentication and owner scoping are not implemented, so do not expose these routes publicly.

## Start on Windows PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env` and replace the example PostgreSQL and MinIO passwords. If you change `POSTGRES_DB`, `POSTGRES_USER`, or `POSTGRES_PASSWORD`, update `DATABASE_URL` to match. `DATABASE_URL`, `REDIS_URL`, and `MINIO_ENDPOINT` point at the host ports because Python runs on the host. `.env` is ignored by Git; never commit credentials.

```powershell
docker compose up -d --wait
alembic upgrade head
python -m server.storage.bootstrap
python -m uvicorn server.main:app --reload
```

The first `docker compose up` builds the local MinIO server image from the pinned official source release `RELEASE.2025-10-15T17-29-55Z` using Docker's Go builder image; it may take several minutes. No host Go installation or MinIO registry login is needed. The MinIO bucket bootstrap is safe to repeat. It creates the bucket named by `MINIO_BUCKET` if needed. Open a second activated terminal for the worker:

```powershell
python -m server.workers.worker
```

The worker uses RQ's `SpawnWorker` on Windows and the regular `Worker` elsewhere. There are no product jobs yet. Verify the API in another terminal:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok"}`. MinIO's API is at `http://127.0.0.1:9000`; its console is at `http://127.0.0.1:9001` and uses the credentials from `.env`.

## Start on macOS or Linux

Use `python3 -m venv .venv`, `source .venv/bin/activate`, `python -m pip install -r requirements.txt`, and `[ -e .env ] || cp .env.example .env`; then run the same `docker compose`, `alembic`, bucket-bootstrap, Uvicorn, and worker commands above. Verify with `curl http://127.0.0.1:8000/health`.

## Checks and shutdown

```powershell
docker compose ps
python -m pytest
```

`GET /health` checks only that the API responds; it does not query dependencies. `alembic upgrade head` creates the first users, devices, and captures tables. `python -m server.storage.bootstrap` checks MinIO access. The worker connects to Redis on startup. For direct checks, run:

```powershell
python -c "from sqlalchemy import text; from server.database.session import get_engine; print(get_engine().connect().execute(text('select 1')).scalar())"
python -c "from server.workers.queue import create_redis_connection; print(create_redis_connection().ping())"
python -c "from server.storage.s3 import create_s3_client; print(create_s3_client().list_buckets()['Buckets'])"
```

Stop Uvicorn and the worker with Ctrl+C. Stop containers while retaining data with `docker compose down`. To **delete all local PostgreSQL and MinIO data**, use `docker compose down -v` only when you intend to reset the environment. Redis has no persistent local volume.

## Developer scripts and infrastructure verification

The [developer scripts index](scripts/README.md) lists local utilities and detailed guides for MinIO image smoke testing and Redis/RQ queue testing and inspection. These scripts are for local verification and debugging, not production entrypoints.

## Project boundaries

Configuration is loaded centrally in `server/config.py` from `.env` and environment variables. `server/database/` owns SQLAlchemy and Alembic, `server/workers/` owns RQ setup, and `server/storage/` owns the S3 client. API routes must call services and must not access these implementations directly. Add new variables to `.env.example` when an integration needs them; keep domain code free of infrastructure settings.
