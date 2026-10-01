# Conceptual data model

**DECIDED:** PostgreSQL is the system of record for metadata, processing state, derived results, and timeline segments. SQLAlchemy 2.x is the persistence mapper; Alembic manages schema migrations. This document defines concepts and relationships, not a final physical schema. Screenshot bytes live in S3-compatible object storage; PostgreSQL holds an object key and necessary image metadata.

## Entities and ownership

| Concept | Ownership and meaning | Cardinality / relationship |
| --- | --- | --- |
| `User` | Owns activity history and access to associated data. | One user has many devices and activity segments. |
| `Device` | Source of captures; belongs to one user. | One device has many captures; each capture belongs to one device. |
| `Capture` | One timestamped screenshot observation, with image reference and processing state. | One capture belongs to one device; its owner is derived through that device. |
| `OCRResult` | Text extracted from one capture, without activity interpretation. | Belongs to one capture. The effective/current result is at most one per capture; history/versioning is TODO. |
| `AnalysisResult` | Semantic interpretation of one capture's OCR text and context. | Belongs to one capture. The effective/current result is at most one per capture; history/versioning is TODO. |
| `ActivitySegment` | An interval of related activity built from multiple observations. | Belongs to one user; may be associated with a device or multiple devices (TODO). Segment-to-capture linkage is TODO. |

**DECIDED foreign-key expectations:** `Device -> User`, `Capture -> Device`, `OCRResult -> Capture`, `AnalysisResult -> Capture`, and `ActivitySegment -> User`. The exact key types and whether redundant owner keys are stored are **TODO**. A segment must never be inferred to cover a missing interval solely because one screenshot preceded it.

## Invariants and uniqueness

- **DECIDED:** A capture has an identity, `captured_at` timestamp, processing state, and image object reference/metadata. Its explicitly agreed transitions are `pending -> processing` and `processing -> completed`. How it enters `failed` and whether it can be retried are **TODO** in [the state-machine ADR](adr/0006-capture-processing-state-machine.md).
- **TODO:** Define result versioning and duplicate handling for repeated jobs before choosing uniqueness constraints.
- **PROPOSED:** If a capture collection endpoint is added, order by `captured_at DESC, id DESC` and use both values for cursor pagination. The access pattern and index design remain TODO.
- **PROPOSED:** Use repository operations that atomically claim `pending` work and commit state/results to prevent duplicate processing. Transaction boundaries and unique constraints are **TODO** in the physical design.
- **TODO:** Client upload deduplication/idempotency key and any uniqueness rule for captures from the same device/time. Do not assume timestamps are unique.

## Expected access patterns

1. Create a capture and retrieve it by identity and owner.
2. Read its state, image reference, OCR result, and analysis result for the capture endpoints.
3. Load a capture/image for a worker, process it, and persist results and state; duplicate handling is TODO.
4. If a capture collection endpoint is added, list captures for an owner; sorting and pagination remain TODO.
5. Read observations by user/device and time range to build segments; read a user's segments over a time range. Aggregation and pagination remain TODO.

## Lifecycle and deletion

**TODO:** Define retention periods and whether deleting a user/device/capture cascades to derived rows, activity segments, and object-storage images. Define orphan-object cleanup after partial intake, provider data handling, reprocessing/result-version history, and how segment provenance is stored. The implementation must not silently choose these policies.
