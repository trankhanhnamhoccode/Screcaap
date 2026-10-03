# Frontend integration contract audit

Source: [api-contract.md](api-contract.md), read completely before implementation.
This audit does not modify or finalize the public contract.

## Operations

| Endpoint | Decided behavior | Needs confirmation |
| --- | --- | --- |
| POST /v1/captures | Async acceptance; 202 only after persistence/enqueue; initial pending state | Encoding/content type, metadata, timestamps, device/owner access, response fields, limits, idempotency |
| GET /v1/captures/{capture_id} | One observation; pending/processing valid; failed persisted; unknown capture 404 | Identifier syntax, metadata/state fields, ownership, errors |
| GET /v1/captures/{capture_id}/image | Stored screenshot, owner scoped; unknown capture 404 | Bytes versus redirect, media types, availability/errors, access control |
| GET /v1/captures/{capture_id}/text | OCR distinct from classification; unknown capture 404 | OCR schema, absent versus empty, pending/failed availability, ownership |
| GET /v1/timeline | Inferred intervals over selected range; recent captures may be absent; gaps stay unassigned | Filter names/bounds/defaults, segment fields, ordering, cursor/pagination, ownership |

**Endpoints currently called: none.** Request/response DTOs for every operation
are **Needs confirmation**. Illustrative placeholder keys are not wire fields.
The only finalized value representation is the processing-state union:
pending, processing, completed, failed.

No health/status endpoint exists in this contract. The earlier `/health` call
was removed although the backend implements it. No backend code or contract
was changed in this task.

## Architecture and error mapping

`App → useTimeline → timelineService` supports loading, readiness, ready/empty
and error. Once filters/response fields are finalized, the service will call
the reusable client with an exact decoder. Selected date is UI state, not a
guessed wire parameter. Until then the service returns a frontend-only typed
readiness result without issuing an unbounded request.

`captureService.getReadiness()` and `healthService.getReadiness()` describe
contract blockers. They are readiness methods, not implemented upload or health
operations. No fake upload arguments, POST requests, state extraction, auth
headers, or polling loops are added.

The existing `services/apiClient.ts` provides typed decoded JSON GET results,
Accept headers, cancellation, and a 10-second timeout including body reading.
`ApiError` distinguishes network, timeout, backend HTTP, and invalid-response;
HTTP errors include status. It does not assume an error JSON envelope, log
payloads, or automatically retry. The owning hook ignores canceled results.
Mutation support waits for a documented encoding/content type.

`api/config.ts` centralizes public URL/timeout/mock configuration. `api/types.ts`
defines the decided processing union and frontend readiness, without fabricating
DTOs. Existing activity/session types remain separate UI/view models.

## Findings

| Classification | Finding | Resolution |
| --- | --- | --- |
| Missing contract | Backend health exists but public contract omits it | Removed call; Needs confirmation |
| Contract ambiguity | Capture/timeline wire shapes are TODO | No invented DTOs, upload encoding, or pagination |
| Frontend bug | Default history/session used fixtures | Explicit development-only mode; normal path uses services |
| Frontend bug | Missing latest capture displayed as no captures | Normal mode displays Unavailable |
| Backend/frontend mismatch | Backend resource routes/services are scaffolds | Reported; no backend redesign |
| Missing contract | Latest capture/session metadata source unspecified | Never derive from timeline/date selection |

## Privacy, lifecycle and assumptions

Tracking remains client side, starts STOPPED, and never restarts on recovery.
Controls do not enable capture; the UI says screenshots are not being captured.
No images, OCR, tokens, or sensitive responses are logged or stored. Processing
failure differs from upload failure; neither is retried automatically.

Mocks require both Vite DEV and VITE_USE_MOCK_API=true; production cannot display
fixture history/status. Newest-first rendering is a UI choice, not API ordering.
Other frontend choices: a 10-second timeout and default local URL already
documented in docs/development.md. No backend behavior is assumed.

## Verification

`npm.cmd run build`: passed TypeScript checking and Vite bundling.
`git diff --check`: passed (line-ending warnings only).
No suitable frontend test runner or lint/test scripts exist; no framework added.
Browser interaction/console checks were not performed: this session has no
browser automation tool. Real network/processing scenarios require missing
contracts and backend implementation. README contains manual checks.

## Needs confirmation

- Timeline filters/bounds, DTOs, ordering and pagination.
- Capture encoding, metadata, response DTOs, identifiers/timestamps, validation.
- Owner authentication/device enrollment and optional structured errors.
- Health endpoint inclusion, response and readiness semantics; backend CORS origins.
- Latest capture source independent of history/date selection.
- Image/OCR delivery and absent-result behavior.
- Explicit retry/idempotency policy. After status fields are defined, select a
  conservative frontend polling interval and finite deadline; stop at terminal
  states and cancel on unmount or Stop.
