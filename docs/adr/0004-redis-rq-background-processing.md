# ADR 0004: Redis and RQ for background processing

## Context

OCR and semantic analysis must run outside the capture upload request. The worker needs a simple job transport for the MVP.

## Decision

Use Redis + RQ as the MVP queue implementation. Background processing assumes at-least-once delivery, so duplicate jobs are possible and processing jobs must be idempotent. Application services depend on a queue/processing abstraction; RQ-specific enqueue and worker code stays in infrastructure/worker entry points. API and worker share the same codebase.

## Consequences

Local and deployed environments need Redis and a worker process. Conditional PostgreSQL state updates now provide atomic claiming; a losing duplicate job skips processing. The claim is committed before processor work. Retry/backoff policy, stale processing recovery, job timeout, queue-specific delivery/recovery details, and consistency between persistence and enqueueing remain TODO. This decision does not introduce an event bus or event-sourcing architecture.
