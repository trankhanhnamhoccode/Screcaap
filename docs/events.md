# Capture lifecycle and application events

**DECIDED:** These names describe application facts and handoffs. They do not require Kafka, RabbitMQ, an event bus, or event sourcing. Redis + RQ is the selected MVP job infrastructure; an RQ job is not automatically a durable publication of every application event.

| Event | When it is true | Producer / use |
| --- | --- | --- |
| `capture.created` | Capture metadata and image have been accepted for processing, with state `pending`. | Intake service; request background processing. |
| `capture.processing.started` | A worker successfully claims a `pending` capture and sets `processing`. | Processing service; lifecycle visibility. |
| `capture.ocr.completed` | OCR output has been persisted for a capture. | Processing service; input to semantic analysis. |
| `capture.analysis.completed` | Semantic analysis has been persisted for a capture. | Processing service; input to timeline aggregation. |
| `capture.processing.completed` | Required processing has finished and state becomes `completed`. | Processing service; client-visible state. |
| `capture.processing.failed` | A processing attempt fails and state changes from `processing` to `failed`. | Processing service; failure reporting and recovery policy are TODO. |

**DECIDED:** Do not include screenshot bytes, raw OCR text, or sensitive provider payloads in job/event payloads; pass a capture reference and load authoritative data through application abstractions. Retry changes `failed` to `pending` only when explicitly requested. Background processing assumes at-least-once delivery, so duplicate jobs are possible. An atomic claim makes duplicate jobs skip processing when the capture is already processing, completed, or failed. Queue-specific delivery/recovery details remain **TODO**.

**IMPLEMENTED queue handoff and worker service:** `RqProcessingQueue` produces a job on `capture-processing` with one positional `capture_id` UUID string. The job target is injected by infrastructure composition; no production consumer is implemented yet. The application worker service accepts a UUID, commits an atomic claim before calling an opaque `CaptureProcessor`, then commits `completed` or `failed`. It surfaces processing errors after persisting `failed`. A production RQ callable and pipeline are deferred until the real processor can be composed.

**TODO:** Define whether these facts need persisted event records, their exact envelope, failure categorization, retry trigger/API, backoff, and publication consistency with PostgreSQL/object storage. No external event contract is established here.
