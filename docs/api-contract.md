# MVP public API contract

This document fixes resource behavior and known semantics. **DECIDED** means agreed for the MVP, **PROPOSED** is a nonbinding implementation direction, and **TODO** requires a product/API decision before an exact wire schema can be implemented. Example placeholders in angle brackets are explanatory, not literal field values or a finalized schema.

## Shared rules

- **DECIDED:** Endpoints are resource oriented and versioned under `/v1`. The API does not expose OCR provider, analyzer, Redis/RQ, or object-storage operations.
- **DECIDED:** A capture is one observation at `captured_at`. Its state is `pending`, `processing`, `completed`, or `failed`; only the transitions in [the state-machine ADR](adr/0006-capture-processing-state-machine.md) are valid.
- **DECIDED:** A successful upload returns `202 Accepted` only after capture metadata/image are persisted and a processing job is enqueued. It does not wait for OCR, analysis, or timeline aggregation.
- **DECIDED:** If capture collections are exposed, use cursor/keyset pagination ordered by `captured_at DESC, id DESC`, with `id` as the stable tie-breaker. Cursor encoding/wire format remains **TODO**.
- **TODO:** Authentication mechanism, principal/device enrollment, authorization responses, upload limits and allowed media types, client idempotency key, and rate limits. Identifier, timestamp, and error formats for endpoints other than POST intake and GET by ID remain undecided. Access to a user's screenshots and derived data must be owner scoped. Until authentication is decided, no endpoint should be treated as safe for public deployment.

The POST intake and GET by ID fields and known error bodies are specified below. Examples for other endpoints remain illustrative.

## `POST /v1/captures`

**Purpose:** Accept one timestamped screenshot observation for asynchronous processing.

- **Authentication:** **TODO** mechanism; only the owning user/device may upload.
- **Request:** `multipart/form-data` with required `device_id` (UUID), `captured_at` (timezone-aware ISO-8601 timestamp), and `image` (file). Screenshot bytes are not sent as JSON.
- **Validation:** FastAPI rejects malformed or missing fields with `422`; a timestamp without an offset is rejected. Empty image files return `422` with `empty_image`. The API does not decode the image. **TODO:** Upload-size limit and exact MIME allowlist; authentication and owner verification.
- **Response:** `202 Accepted` with JSON fields `id`, `device_id`, `captured_at`, `processing_status`, `created_at`, and `updated_at`. State comes from the persisted application result, normally `pending`. The response does not expose an image reference, storage details, or a queue job ID. `Location` header policy remains **TODO**.
- **Errors:** Unknown device: `404` with `device_not_found`. Enqueue failure after commit: `503` with `capture_enqueue_failed` and the committed `capture_id`. Storage or persistence failure: generic `500` without provider details. If production processing is not configured, the default dependency returns `503` with `capture_processing_unavailable` before intake.
- **Known application error body:** `{"error":{"code":"capture_enqueue_failed","message":"Capture was stored but background processing could not be scheduled.","capture_id":"<UUID>"}}`. Missing-device and empty-image errors use the same `error` object without `capture_id`. FastAPI field validation retains its standard `detail` body; the pre-intake configuration `503` currently uses `{"detail":{"code":"capture_processing_unavailable"}}`.
- **Asynchronous semantics:** `202` means the Capture was accepted for asynchronous processing and a job was requested; OCR and semantic analysis have not completed. Enqueue failure leaves the image and pending Capture stored. Blind retry may create another Capture because upload idempotency and recovery are **TODO**. `GET /v1/captures/{capture_id}` exposes the current persisted state.

Example exchange:

```http
POST /v1/captures
Content-Type: multipart/form-data; boundary=...

device_id=<UUID>
captured_at=2026-10-03T01:23:45+07:00
image=<uploaded file>

HTTP/1.1 202 Accepted
Content-Type: application/json

{"id":"<UUID>","device_id":"<UUID>","captured_at":"2026-10-03T01:23:45+07:00","processing_status":"pending","created_at":"2026-10-02T18:23:46Z","updated_at":"2026-10-02T18:23:46Z"}
```

## `GET /v1/captures/{capture_id}`

**Purpose:** Retrieve one Capture's persisted metadata and processing state without starting or changing processing.

- **Authentication:** Not implemented. Owner-scoped authorization is **TODO**; possession of a Capture UUID must not grant access in the final product. Do not expose this endpoint publicly until access control exists.
- **Request:** `capture_id` is a UUID path parameter; no body.
- **Validation:** FastAPI rejects an invalid UUID with `422` and its standard validation body. Ownership validation is **TODO**.
- **Response:** `200 OK` with the same public Capture schema as POST: `id`, `device_id`, `captured_at`, `processing_status`, `created_at`, and `updated_at`. The status is read from PostgreSQL and may be `pending`, `processing`, `completed`, or `failed`. Image references, storage keys, and queue information are excluded.
- **Errors:** Unknown Capture: `404` with `{"error":{"code":"capture_not_found","message":"Capture was not found."}}`. Inaccessible-resource behavior (`403` versus `404`) and authentication failure remain **TODO**.
- **Read semantics:** The request uses the read application service and repository only. It does not consult Redis/RQ or MinIO, enqueue work, or change the Capture. A single screenshot is not a period-long activity claim.

```http
GET /v1/captures/8c753daf-69fb-47b7-bc9a-97b4c8b48029

HTTP/1.1 200 OK
Content-Type: application/json

{"id":"8c753daf-69fb-47b7-bc9a-97b4c8b48029","device_id":"<UUID>","captured_at":"2026-10-03T01:23:45+07:00","processing_status":"processing","created_at":"2026-10-02T18:23:46Z","updated_at":"2026-10-02T18:23:47Z"}
```

## `GET /v1/captures/{capture_id}/image`

**Purpose:** Retrieve the stored screenshot belonging to a capture, subject to access control.

- **Authentication:** **TODO** mechanism; owner scoped.
- **Request:** Capture identifier in path; no body. Optional image transformation parameters are not part of this MVP contract.
- **Validation:** Validate identifier and ownership. Image availability and supported content types are **TODO**.
- **Response:** Image bytes or a controlled redirect/signed URL are **TODO** delivery choices. The response must preserve the stored image's applicable media type; headers/cache behavior are **TODO**.
- **Status codes/errors:** `200 OK` for a direct byte response, or a redirect status if redirect delivery is chosen (**TODO**). Unknown capture: `404`. Missing object, inaccessible resource, and unavailable storage mappings are **TODO**. Authentication failure is **TODO**.
- **Asynchronous semantics:** Image should be retrievable after successful intake even while analysis is pending, subject to the delivery choice and storage availability.

```http
GET /v1/captures/<capture_id>/image

HTTP/1.1 200 OK
Content-Type: <stored image media type>

<image bytes; direct-byte delivery is illustrative, not selected>
```

## `GET /v1/captures/{capture_id}/text`

**Purpose:** Retrieve the OCR output for one capture. OCR is visible text, not an activity classification.

- **Authentication:** **TODO** mechanism; owner scoped.
- **Request:** Capture identifier in path; no body.
- **Validation:** Validate identifier and ownership. Exact identifier syntax is **TODO**.
- **Response:** `200 OK` when OCR output exists. Exact OCR schema, text layout, confidence representation, and field names are **TODO**.
- **Errors:** Unknown capture: `404`. Pending/processing capture without OCR, failed capture without OCR, inaccessible resource, and authentication responses are **TODO**; do not conflate an absent OCR result with an empty OCR result.
- **Asynchronous semantics:** OCR may become available before final capture completion. A failed later stage may still leave a persisted OCR result; exposure policy is **TODO**.

```http
GET /v1/captures/<capture_id>/text

HTTP/1.1 200 OK
Content-Type: application/json

{"<OCR result representation TODO>": "<extracted text or structured output>"}
```

## `GET /v1/timeline`

**Purpose:** Read the user's aggregated `ActivitySegment` intervals over a selected time range.

- **Authentication:** **TODO** mechanism; owner scoped.
- **Request:** Time-range filters; cursor/page size are proposed options. Exact parameter names, required/default range, inclusive/exclusive bounds, device filtering, and pagination are **TODO**.
- **Validation:** Validate time range, cursor, page size, and owner scope. Exact error mapping is **TODO**.
- **Response:** `200 OK` with activity segments for the requested period. Segment fields, ordering, pagination envelope, and tie-breaking order are **TODO**. Each segment is an inferred interval, not a guarantee that the user was active through an unsampled gap.
- **Errors:** Invalid range/cursor (`400` or `422`: **TODO** mapping), inaccessible resource/authentication (**TODO**), and server errors (`5xx`; body **TODO**).
- **Asynchronous semantics:** Recently accepted captures may not yet appear in the timeline. The API must not silently fill large missing intervals with the prior activity.

```http
GET /v1/timeline?<time-range parameters TODO>&<cursor parameter TODO>

HTTP/1.1 200 OK
Content-Type: application/json

{"<segments field TODO>": ["<ActivitySegment representation TODO>"], "<next cursor field TODO>": "<opaque cursor or end marker>"}
```

**PROPOSED:** Use an opaque cursor that carries the last item’s complete sort key and is scoped to the same filters. **TODO:** Select timeline segment ordering/tie-breaker and whether a stable snapshot is needed while aggregation changes results. These choices must be settled before finalizing the wire cursor.
