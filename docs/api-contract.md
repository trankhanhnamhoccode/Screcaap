# MVP public API contract

This document fixes resource behavior and known semantics. **DECIDED** means agreed for the MVP, **PROPOSED** is a nonbinding implementation direction, and **TODO** requires a product/API decision before an exact wire schema can be implemented. Example placeholders in angle brackets are explanatory, not literal field values or a finalized schema.

## Shared rules

- **DECIDED:** Endpoints are resource oriented and versioned under `/v1`. The API does not expose OCR provider, analyzer, Redis/RQ, or object-storage operations.
- **DECIDED:** A capture is one observation at `captured_at`. Its state is `pending`, `processing`, `completed`, or `failed`; only the transitions in [the state-machine ADR](adr/0006-capture-processing-state-machine.md) are valid.
- **DECIDED:** A successful upload returns `202 Accepted` only after capture metadata/image are persisted and a processing job is enqueued. It does not wait for OCR, analysis, or timeline aggregation.
- **PROPOSED:** If capture collections are exposed, order by `captured_at DESC, id DESC` and use keyset/cursor pagination. Strategy and wire format remain **TODO** decisions.
- **TODO:** Authentication mechanism, principal/device enrollment, authorization responses, identifier format, timestamp serialization, error body schema, upload limits and allowed media types, client idempotency key, and rate limits. Access to a user's screenshots and derived data must be owner scoped. Until authentication is decided, no endpoint should be treated as safe for public deployment.

The response examples show only decided semantic members. Their field spelling and envelope remain **TODO** unless explicitly stated below.

## `POST /v1/captures`

**Purpose:** Accept one timestamped screenshot observation for asynchronous processing.

- **Authentication:** **TODO** mechanism; only the owning user/device may upload.
- **Request:** Screenshot bytes and observation metadata including capture time and device association. **TODO:** multipart versus another upload format, field names, identifier format, timezone wire format, content types, size limit, and optional client deduplication token.
- **Validation:** Require a usable image, capture timestamp, and device association; enforce ownership and eventual size/type limits. Exact validation ranges and error shape are **TODO**.
- **Response:** `202 Accepted` with a way to identify the capture and its initial `pending` state. Exact JSON field names and `Location` header policy are **TODO**.
- **Errors:** Validation failure (`400` or `422`: **TODO** mapping); unauthenticated/forbidden (`401`/`403`: **TODO** policy); upload too large (`413` if a limit is set); persistence/storage/enqueue failure (`5xx`, exact mapping **TODO**). The API must not report acceptance if the job was not successfully requested.
- **Asynchronous semantics:** The client polls `GET /v1/captures/{capture_id}` for state. A `202` does not promise that OCR or timeline data already exists. Intake idempotency and recovery from partial persistence are **TODO**.

Illustrative exchange, with wire names and body encoding still **TODO**:

```http
POST /v1/captures
Content-Type: <upload media type TODO>

<image bytes and captured_at/device metadata; encoding TODO>

HTTP/1.1 202 Accepted
Content-Type: application/json

{"<capture identifier field TODO>": "<id>", "<state field TODO>": "pending"}
```

## `GET /v1/captures/{capture_id}`

**Purpose:** Retrieve one capture's metadata and processing state.

- **Authentication:** **TODO** mechanism; owner scoped.
- **Request:** Capture identifier in path; no body. Identifier syntax is **TODO**.
- **Validation:** Reject malformed identifiers; verify ownership. Exact malformed-ID status is **TODO**.
- **Response:** `200 OK` with identity, observation timestamp, and one documented processing state. Other metadata and field names are **TODO**. This endpoint must not treat a screenshot as a period-long activity claim.
- **Errors:** `404 Not Found` for an unknown capture; inaccessible-resource behavior (`403` versus `404`) and general error body are **TODO**. Authentication failure is **TODO**.
- **Asynchronous semantics:** `pending` and `processing` are valid successful reads; `failed` is a persisted state, not a GET failure status.

```http
GET /v1/captures/<capture_id>

HTTP/1.1 200 OK
Content-Type: application/json

{"<id field TODO>": "<id>", "<captured_at field TODO>": "<timestamp>", "<state field TODO>": "processing"}
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
