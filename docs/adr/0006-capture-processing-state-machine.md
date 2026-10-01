# ADR 0006: Capture processing state machine

## Context

Clients need to observe asynchronous progress, and workers may receive a job more than once. Retrying failed work must be deliberate.

## Decision

Use `pending`, `processing`, `completed`, and `failed`. The transitions are `pending -> processing`, `processing -> completed`, `processing -> failed`, and `failed -> pending` only through explicit retry. There is no implicit `completed -> processing` transition. Treat persisted state as authoritative.

## Consequences

Workers must claim work safely and avoid duplicate OCR, analysis, or timeline effects when jobs repeat. The exact retry API, stale `processing` recovery, failure representation, result versioning, and transaction/constraint design remain TODO.
