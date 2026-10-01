# ADR 0004: Redis and RQ for background processing

## Context

OCR and semantic analysis must run outside the capture upload request. The worker needs a simple job transport for the MVP.

## Decision

Use Redis + RQ as the MVP queue implementation. Application services depend on a queue/processing abstraction; RQ-specific enqueue and worker code stays in infrastructure/worker entry points. API and worker share the same codebase.

## Consequences

Local and deployed environments need Redis and a worker process. Delivery assumptions, duplicate handling, retry/backoff policy, job timeout, and consistency between persistence and enqueueing remain TODO. This decision does not introduce an event bus or event-sourcing architecture.
