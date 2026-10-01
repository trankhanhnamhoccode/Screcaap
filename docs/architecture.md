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

**DECIDED worker flow:** `job -> Capture -> OCRProvider -> ActivityAnalyzer -> persist results -> timeline aggregation`. The worker invokes application services. OCR output is distinct from semantic analysis. An `ActivitySegment` represents an interval inferred from observations; a `Capture` represents only one timestamp.

**TODO:** Define the consistency mechanism between PostgreSQL, object storage, and job enqueueing, including recovery from partial intake and enqueue failure. No distributed transaction is assumed.

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

**DECIDED:** Capture states are `pending`, `processing`, `completed`, and `failed`. The specified transitions are `pending -> processing` and `processing -> completed`. Entry into `failed` and retry transitions remain **TODO**. See [the state-machine ADR](adr/0006-capture-processing-state-machine.md).

**TODO:** Define delivery assumptions, duplicate handling, idempotency, and recovery before implementing RQ jobs. Persisted state is authoritative, not queue delivery count.

**DECIDED:** Timeline segments are inferred from multiple observations. A screenshot does not establish activity through the next screenshot timestamp. The aggregation algorithm, gap threshold, and treatment of low-confidence observations are **TODO**; [Proposal 0008](adr/0008-rule-based-timeline-aggregation.md) is one option.

## Privacy and operations

- **DECIDED:** Store screenshot bytes in object storage and only metadata/object keys in PostgreSQL. Restrict access to images, OCR text, and interpretations to their owner once authentication is defined.
- **DECIDED:** Do not log screenshot bytes, unnecessary OCR text, secrets, authorization headers, or full sensitive provider payloads. Keep credentials in environment variables.
- **TODO:** Authentication and authorization mechanism, retention/deletion policy, upload size and media validation limits, encryption/access controls, observability and alerting, queue retry/backoff policy, and deployment topology beyond Docker Compose.

This architecture adds no separate event broker or service boundary. [Application events](events.md) name lifecycle facts; Redis/RQ is the selected job transport, not an event-sourcing architecture.
