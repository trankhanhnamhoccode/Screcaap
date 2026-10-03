# ADR 0006: Capture processing state machine

## Context

Clients need to observe asynchronous progress, and workers may receive a job more than once. Retrying failed work must be deliberate.

## Decision

Use `pending`, `processing`, `completed`, and `failed`. The transitions are `pending -> processing`, `processing -> completed`, `processing -> failed`, and `failed -> pending` only through explicit retry. There is no implicit `completed -> processing` transition. Treat persisted state as authoritative.

## Consequences

Workers use conditional updates to claim `pending` work atomically. A worker commits the claim before running its processor, then commits `completed` or `failed`. Jobs that find `processing`, `completed`, or `failed` skip processing. Missing captures surface an error. The exact retry API, stale `processing` recovery, completion persistence failure recovery, failure representation, result versioning, and derived-result transaction design remain TODO.
