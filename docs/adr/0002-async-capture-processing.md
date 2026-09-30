# ADR 0002: Asynchronous capture processing

## Context

OCR and LLM latency vary, and external providers may fail. Upload response time should not depend on analysis time. Background work should eventually support retries.

## Decision

`POST /v1/captures` stores the capture and schedules processing, then returns `202 Accepted`. OCR, analysis, and timeline work happen outside the request path.

## Consequences

The API can respond promptly, and processing can retry independently. Clients need a way to observe pending, completed, and failed work. Scheduling technology, consistency guarantees, and retry policy remain TODO decisions.
