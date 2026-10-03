# Backend architecture

## Status and scope

**DECIDED:** The MVP is a modular monolith with a background worker. The API and worker share one codebase and application/domain code, but run as separate runtime processes. This document describes the target architecture; the current repository is a scaffold, not a running backend.

**DECIDED stack:** Python, FastAPI, Pydantic v2, PostgreSQL, SQLAlchemy 2.x, Alembic, Redis, RQ, pytest, Docker Compose, an S3-compatible object storage abstraction, and MinIO for local development.

## Runtime components and flow

| Component | Responsibility |
| --- | --- |
| Desktop client | Periodically capture a screenshot and submit the observation. |
| FastAPI process | Parse and validate transport data, call application services, return HTTP responses. |
| Application services | Coordinate intake, reads, processing, retries, and timeline aggregation through abstractions. |
| PostgreSQL | Persist users, devices, capture metadata and state, derived results, and activity segments. Screenshot bytes do not belong here. |
| S3-compatible object storage | Hold screenshot bytes; MinIO supplies this interface in local development. |
| Redis + RQ | MVP queue implementation for background jobs. Application code depends on a queue/processing abstraction. |
| Worker process | Consume jobs and invoke application processing use cases from the same codebase. |
| OCR provider | Extract visible text only; PP-OCRv5 Mobile is the intended adapter. |
| Activity analyzer | Interpret OCR text and capture context; OpenRouter is the intended integration. |
| Timeline aggregator | Build intervals from ordered observations using deterministic MVP rules. |

**DECIDED upload flow:** `Desktop Client -> POST /v1/captures -> persist metadata/image -> enqueue job -> 202 Accepted`. The response must not wait for OCR or analysis. The service coordinates persistence and enqueueing; the API route performs no storage or queue work itself.

**IMPLEMENTED application intake flow:** `CaptureIntakeCommand(device_id, captured_at, image_bytes) -> look up Device -> ImageStorage.store -> add pending Capture -> commit -> ProcessingQueue.enqueue_capture_processing(capture_id) -> Capture`. The application owns commit/rollback through the caller-provided SQLAlchemy Session's transaction methods; repositories never commit. `ImageStorage` and `ProcessingQueue` are application ports, without storage or queue SDK types. MinIO implements the image port using opaque object keys; `RqProcessingQueue` implements the queue port using a capture ID string. `POST /v1/captures` parses multipart data and calls this service through request-scoped dependency injection. The production queue dependency returns `503` before intake until a real job target and processor pipeline exist; tests inject a fake queue. The production capture-processing worker is not implemented yet.

**IMPLEMENTED capture read flow:** `GET /v1/captures/{capture_id} -> CaptureReadService -> CaptureRepository.get_by_id -> PostgreSQL`. It uses a read-only request-scoped session and returns persisted status through the same public schema as POST. The read does not use MinIO, Redis/RQ, or the worker. Owner-scoped authorization remains TODO.

If the device is missing, no image, capture, or job is created. Storage failure prevents capture persistence and enqueueing. A repository/add or commit failure triggers rollback and best-effort image removal while preserving the original error. Enqueue failure happens after commit: the pending Capture and image remain, and the service raises an error containing the committed capture ID. **TODO:** Recover pending captures whose enqueue failed; this MVP has no outbox, retry, or reconciliation mechanism.

**DECIDED worker flow:** `job -> Capture -> OCRProvider -> ActivityAnalyzer -> persist results -> timeline aggregation`. The worker invokes application services. OCR output is distinct from semantic analysis. An `ActivitySegment` represents an interval inferred from observations; a `Capture` represents only one timestamp.

**TODO:** Define a durable consistency/recovery mechanism between PostgreSQL, object storage, and job enqueueing. Best-effort image cleanup cannot guarantee orphan removal, and enqueue-after-commit does not guarantee that a pending capture has a queued job. No distributed transaction is assumed.

## Layers and dependency direction

```text
API / Transport (server/api, shared/schemas)
          -> Application / Services (server/services)
          -> Domain and application ports (server/domain, interfaces)
Infrastructure adapters (server/database, server/storage, server/ocr,
server/llm, queue adapter) implement those ports.
Worker entry points (server/workers) call application services.
```

- **API / Transport:** FastAPI routing, request validation with Pydantic v2, dependency wiring, status codes, and response formatting. Routes call services; they do not perform ORM queries, object-storage operations, OCR/model calls, or queue-specific work.
- **Application / Services:** Business use cases and orchestration, including capture intake, state transitions, processing, retrieval, retry requests, and timeline aggregation. Services use repository, `ImageStorage`, `OCRProvider`, `ActivityAnalyzer`, and queue/processing abstractions.
- **Domain:** `Capture`, `OCRResult`, `AnalysisResult`, `ActivitySegment`, and their rules. Domain code does not depend on FastAPI, Pydantic transport models, SQLAlchemy, Redis/RQ, MinIO/S3 SDKs, OCR implementations, or LLM providers.
- **Infrastructure:** SQLAlchemy repositories and Alembic migrations, object storage adapter, Redis/RQ adapter, OCR adapter, and analyzer adapter. Provider SDK details stay inside their adapters.

The composition boundary wires concrete adapters to ports. `shared/schemas/` contains transport schemas, not ORM entities or provider implementations. The public API exposes resources and states, never PaddleOCR, OpenRouter, Redis, or RQ commands.

## Processing reliability

**DECIDED:** Capture states are `pending`, `processing`, `completed`, and `failed`. The transitions are `pending -> processing`, `processing -> completed`, `processing -> failed`, and `failed -> pending` only through explicit retry. There is no implicit `completed -> processing` transition. See [the state-machine ADR](adr/0006-capture-processing-state-machine.md).

**DECIDED:** Background processing assumes at-least-once delivery, so duplicate jobs are possible and processing jobs must be idempotent. Persisted state is authoritative, not queue delivery count.

**IMPLEMENTED worker orchestration foundation:** A worker service receives a Capture ID, atomically claims `pending -> processing`, and commits that claim before invoking the opaque `CaptureProcessor` port. The processor runs outside a database transaction. On success, the service commits `processing -> completed`; on a processing exception, it commits `processing -> failed` and surfaces the original error. A losing claim checks persisted state: `processing`, `completed`, and `failed` jobs skip processing; missing captures raise an error. Failed captures are not automatically retried. RQ delivery remains at least once, and the queue adapter still accepts an importable job target. No production target is wired until a real processor exists.

**TODO:** Implement the production processing pipeline, `OCRProvider`, `ActivityAnalyzer`, and result persistence. Define RQ retry/backoff, stale `processing` recovery, explicit `failed -> pending` retry, completion persistence failure recovery, and queue-specific delivery/recovery details. No automatic recovery is implied by the current worker service.

**DECIDED:** Timeline segments are inferred from multiple observations. A screenshot does not establish activity through the next screenshot timestamp. The aggregation algorithm, gap threshold, and treatment of low-confidence observations are **TODO**; [Proposal 0008](adr/0008-rule-based-timeline-aggregation.md) is one option.

## Privacy and operations

- **DECIDED:** Store screenshot bytes in object storage and only metadata/object keys in PostgreSQL. Restrict access to images, OCR text, and interpretations to their owner once authentication is defined.
- **DECIDED:** Do not log screenshot bytes, unnecessary OCR text, secrets, authorization headers, or full sensitive provider payloads. Keep credentials in environment variables.
- **TODO:** Authentication and authorization mechanism, retention/deletion policy, upload size and media validation limits, encryption/access controls, observability and alerting, queue retry/backoff policy, and deployment topology beyond Docker Compose.

This architecture adds no separate event broker or service boundary. [Application events](events.md) name lifecycle facts; Redis/RQ is the selected job transport, not an event-sourcing architecture.
