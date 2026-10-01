# ADR 0006: Capture processing state machine

## Context

Clients need to observe asynchronous progress, and workers may receive a job more than once. Retrying failed work must be deliberate.

## Decision

Use `pending`, `processing`, `completed`, and `failed`. The specified transitions are `pending -> processing` and `processing -> completed`. Entry into `failed` and retry transitions are unresolved. Treat persisted state as authoritative.

## Consequences

Workers must claim work safely and avoid duplicate OCR, analysis, or timeline effects when jobs repeat. The exact retry API, stale `processing` recovery, failure representation, result versioning, and transaction/constraint design remain TODO.
