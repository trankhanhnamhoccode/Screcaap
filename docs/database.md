# Conceptual data model

**Status: conceptual.** The database design teammate owns SQL tables, migrations, keys, constraints, and storage-specific choices. No schema is finalized here.

| Entity | Relationship and role |
| --- | --- |
| User | Owns devices and the resulting activity history. |
| Device | Belongs to a user; originates captures. |
| Capture | Belongs to a device and represents one screenshot observation. Its image lives in image storage. |
| OCRResult | Belongs to a capture; records extracted text only. |
| AnalysisResult | Belongs to a capture; records an interpretation of OCR text and context. |
| ActivitySegment | Belongs to a user's timeline and groups related capture observations over a period. |

Cardinality, exact ownership keys, reprocessing/version history, segment-to-capture association, status representation, image references, indexes, retention rules, and database technology are **TODO** for database design. A capture is not itself an activity segment.
