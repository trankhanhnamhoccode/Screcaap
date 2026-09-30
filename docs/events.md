# Conceptual internal events

These names describe application facts and handoffs. They do not select Kafka, RabbitMQ, Redis, Celery, or any queue technology. The delivery mechanism, retry semantics, and event envelope are TODO.

| Event | Producer | Consumer | Purpose | Minimum conceptual payload |
| --- | --- | --- | --- | --- |
| `capture.created` | Capture service after intake | Background processing boundary | Signal that a stored capture is ready for processing. | Capture identity and a way to locate its stored image. |
| `capture.ocr.completed` | OCR processing step | Analysis step | Make extracted text available for interpretation. | Capture identity and OCR result identity or retrievable reference. |
| `capture.analysis.completed` | Analysis step | Timeline processing | Make an interpretation available for aggregation. | Capture identity and analysis result identity or retrievable reference. |
| `capture.processing.failed` | Processing step that records a failure | Retry/operations handling, design TODO | Record that a capture could not complete a processing stage. | Capture identity, failed stage, and failure reference or category. |

Payloads avoid embedding image data or committing to a transport format. Consumers should load authoritative persisted data through abstractions where needed.
