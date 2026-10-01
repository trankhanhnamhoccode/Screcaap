# ADR 0005: S3-compatible image storage and MinIO local

## Context

Screenshots can be sensitive and large. Keeping their bytes in relational rows would couple image retrieval and retention to metadata persistence.

## Decision

Store screenshot bytes in S3-compatible object storage behind the `ImageStorage` abstraction. Use MinIO for local development. PostgreSQL stores the object key and necessary image metadata, never the screenshot binary.

## Consequences

Local development needs MinIO, and the application must coordinate object and metadata lifecycles. Access control, upload limits, orphan cleanup, retention/deletion, and delivery via direct bytes versus controlled URL remain TODO. Provider SDK use stays inside the storage adapter.
