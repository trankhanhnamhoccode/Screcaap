# Draft API contract

**Status: draft.** The API/database design teammate owns field definitions and final response shapes. All request and response fields below are TODO until agreed. This document records resource and endpoint intent only.

## Resources

| Resource | Concept |
| --- | --- |
| Capture | Screenshot observation and processing state. |
| OCRResult | Text extracted from a capture, without activity interpretation. |
| AnalysisResult | Interpretation of OCR text and capture context. |
| ActivitySegment | Period of related activity in the timeline. |

## Expected endpoints

| Method and path | Intent | Contract status |
| --- | --- | --- |
| `POST /v1/captures` | Accept an image and metadata for asynchronous processing. Return `202 Accepted` after intake and scheduling; do not wait for OCR or LLM. | Request fields, response fields, error shape, and idempotency: TODO. |
| `GET /v1/captures/{capture_id}` | Retrieve capture status and metadata. | Response fields and status semantics: TODO. |
| `GET /v1/captures/{capture_id}/image` | Retrieve the capture image, subject to access policy. | Media type, authorization, and delivery shape: TODO. |
| `GET /v1/captures/{capture_id}/text` | Retrieve OCR text when available. | Pending/failed behavior and response fields: TODO. |
| `GET /v1/timeline` | Retrieve activity segments for a period. | Filters, pagination, and response fields: TODO. |

No route handler or transport schema here is a finalized contract. Authentication, authorization, upload limits, retention, and versioning details remain TODO team decisions.
