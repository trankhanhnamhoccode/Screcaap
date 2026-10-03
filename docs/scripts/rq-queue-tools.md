# Test the Redis/RQ queue adapter

Run commands from the repository root with dependencies installed from `requirements.txt` and a private `.env` copied from `.env.example`. Docker Desktop (or Docker Engine with Compose) must be running. The Redis Compose service is `redis`, exposed on `127.0.0.1:6379`; the host application uses the configured `REDIS_URL` (the example is `redis://127.0.0.1:6379/0`).

## Start and check Redis

```powershell
docker compose up -d --wait redis
docker compose ps redis
python -c "from server.workers.queue import create_redis_connection; print(create_redis_connection().ping())"
```

The Compose status should be `healthy`, and the ping command should print `True`.

## Run integration tests

```powershell
python -m pytest tests/test_rq_processing_queue.py -q
```

The tests enqueue real RQ jobs and delete only their own job IDs. They do not flush Redis or clear the queue. They skip with a start command when Redis is unavailable.

## Smoke test and inspect the queue

```powershell
python scripts/rq_queue_smoke_test.py
```

The script generates a random capture UUID, enqueues one job through `RqProcessingQueue`, fetches it from Redis, and prints the `capture-processing` queue name, RQ job ID, and string `capture_id` payload. It pauses for inspection; press Enter to delete the exact smoke job and verify cleanup. Add `--no-pause` to verify and clean up automatically. An error or interruption also triggers a cleanup attempt.

While the script is paused, use the inspection utility in another terminal. `list` shows the queue name, queued job count, and job IDs:

```powershell
python scripts/rq_queue_inspect.py list
```

Inspect one job's status, queue, function target, and capture ID payload:

```powershell
python scripts/rq_queue_inspect.py show <job-id>
```

The smoke script removes its own job when you press Enter. Run `list` again to confirm its ID is gone. If an earlier interrupted development run left a job behind, inspect it first, then explicitly delete that one queued job:

```powershell
python scripts/rq_queue_inspect.py delete <job-id>
```

`delete` requires a job ID and refuses jobs outside the queued `capture-processing` list. It removes only the selected job's queue entry and stored RQ record. Never assume every job in Redis is a smoke job; do not delete an ID you have not inspected. The tool reads `REDIS_URL` through project settings, so no Redis CLI setup is needed.

## Internal job contract and current limit

`RqProcessingQueue` is the producer. It enqueues exactly one positional `capture_id` argument as a UUID string; it does not enqueue screenshot bytes, domain objects, ORM models, or infrastructure clients. The future capture-processing worker will parse the string into the project's UUID type. The job target is supplied to the adapter by infrastructure composition; no production target exists yet. Tests and the smoke script inject `scripts.rq_smoke_job.echo_capture_id`, which reads or changes no product data. The current worker scaffold listens only to the separate `default` queue, so it does not consume these `capture-processing` smoke jobs. Do not start a capture-processing worker for this smoke test.

Redis/RQ enqueue failures propagate to `CaptureService`. If enqueueing fails after its database commit, `CaptureService` raises `CaptureEnqueueError`; the committed Capture remains `pending` and its image remains stored. Recovery, worker execution, claiming, retries, and idempotency are later milestones.

Stop Redis while preserving development data:

```powershell
docker compose stop redis
```

Do not use `FLUSHDB`, `FLUSHALL`, or `docker compose down -v` for routine cleanup.
