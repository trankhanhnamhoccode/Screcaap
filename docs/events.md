# Capture lifecycle and application events

**DECIDED:** These names describe application facts and handoffs. They do not require Kafka, RabbitMQ, an event bus, or event sourcing. Redis + RQ is the selected MVP job infrastructure; an RQ job is not automatically a durable publication of every application event.

| Event | When it is true | Producer / use |
| --- | --- | --- |
| `capture.created` | Capture metadata and image have been accepted for processing, with state `pending`. | Intake service; request background processing. |
| `capture.processing.started` | A worker successfully claims a `pending` capture and sets `processing`. | Processing service; lifecycle visibility. |
| `capture.ocr.completed` | OCR output has been persisted for a capture. | Processing service; input to semantic analysis. |
| `capture.analysis.completed` | Semantic analysis has been persisted for a capture. | Processing service; input to timeline aggregation. |
| `capture.processing.completed` | Required processing has finished and state becomes `completed`. | Processing service; client-visible state. |
| `capture.processing.failed` | A processing attempt fails; how state becomes `failed` is TODO. | Processing service; failure reporting and recovery policy are TODO. |

**DECIDED:** Do not include screenshot bytes, raw OCR text, or sensitive provider payloads in job/event payloads; pass a capture reference and load authoritative data through application abstractions. Retry transitions and job delivery assumptions are **TODO**.

**TODO:** Define whether these facts need persisted event records, their exact envelope, failure categorization, retry trigger/API, backoff, and publication consistency with PostgreSQL/object storage. No external event contract is established here.
