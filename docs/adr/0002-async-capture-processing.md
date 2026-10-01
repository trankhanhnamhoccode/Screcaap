# ADR 0002: Asynchronous capture processing

## Context

OCR and LLM latency vary, and external providers may fail. Upload response time should not depend on analysis time. Background work should eventually support retries.

## Decision

`POST /v1/captures` stores the capture and schedules processing, then returns `202 Accepted`. OCR, analysis, and timeline work happen outside the request path.

## Consequences

The API can respond promptly, and clients observe work through capture state. Redis + RQ is selected in ADR 0004. The decided transitions are in ADR 0006. Background processing assumes at-least-once delivery, so duplicate jobs are possible and processing jobs must be idempotent. Intake consistency, exact duplicate-job handling, atomic claiming/concurrency, failure recovery, retry/backoff policy, and queue-specific delivery/recovery details remain TODO.
