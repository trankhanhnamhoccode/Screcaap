# Developer scripts

These utilities support local verification, smoke testing, infrastructure inspection, and debugging. They are not production entrypoints. Run them from the repository root with the project's Python environment and private `.env` configured.

| Script | Purpose | Run directly? | Infrastructure | Temporary resources and cleanup | Guide |
| --- | --- | --- | --- | --- | --- |
| [`minio_image_smoke_test.py`](../../scripts/minio_image_smoke_test.py) | Verify a real ImageStorage → MinIO byte round trip. | Yes, with an image path. | MinIO and configured bucket. | Creates one object; deletes and verifies only that object on exit. | [MinIO image smoke test](minio-image-smoke-test.md) |
| [`rq_queue_smoke_test.py`](../../scripts/rq_queue_smoke_test.py) | Verify a real ProcessingQueue → RQ → Redis enqueue. | Yes. | Redis. | Creates one RQ job; deletes and verifies only its own job on exit. | [RQ queue tools](rq-queue-tools.md) |
| [`rq_queue_inspect.py`](../../scripts/rq_queue_inspect.py) | List the capture queue, show one job, or delete one explicitly selected queued job. | Yes. | Redis. | Creates nothing; `delete <job-id>` affects only that ID. | [RQ queue tools](rq-queue-tools.md) |
| [`rq_smoke_job.py`](../../scripts/rq_smoke_job.py) | Importable support callable for RQ tests and the smoke script. | **No.** | Redis only when another tool enqueues it. | Creates nothing by itself; the enqueuing test/script owns cleanup. | [RQ queue tools](rq-queue-tools.md) |
