# Screcaap frontend

React, TypeScript, Vite and plain CSS, with the existing Electron desktop host.
The API framework follows [docs/api-contract.md](../docs/api-contract.md).
Resource paths and lifecycle semantics are defined, but operation wire schemas
are TODOs. Normal mode displays **Needs confirmation** rather than issuing
guessed requests or presenting demo history as real observations.

## Development

From `frontend/`, with Node.js 22 and npm installed:

```powershell
npm.cmd install
Copy-Item .env.example .env.local
npm.cmd run dev
```

`VITE_API_BASE_URL` configures the API root. The default `http://127.0.0.1:8000`
comes from [backend development documentation](../docs/development.md).
All Vite environment values are public: never include credentials. The URL is
embedded at build time; rebuild desktop packages after changes.

Set `VITE_USE_MOCK_API=true` in `.env.local` to preview fixtures in development.
Restart Vite after environment changes. Mock mode is disabled in production,
preview and desktop builds, even when the variable is true. The demo opens on
2 October 2026; normal mode opens on today.

`npm.cmd run build` checks TypeScript and bundles production assets.
`npm.cmd run typecheck` checks types alone; `npm.cmd run preview` serves the build.
No frontend test or lint scripts are configured.

## Integration

`App → useTimeline → timelineService → API client → backend` is the intended
flow. The service currently returns typed readiness because query/response
fields are unspecified. Capture and health services likewise expose readiness.
See [the contract audit](../docs/frontend-integration.md) for operation mappings.

The existing fetch client now accepts a contract-specific response decoder,
distinguishes network/timeout/HTTP/invalid-response errors, supports cancellation,
and applies a 10-second timeout through response reading. No automatic retries,
sensitive logs, invented error envelopes, or guessed transport DTOs are added.

The prior `/health` request was removed: it is absent from the authoritative
contract. Backend status is Needs confirmation in normal mode and explicitly
simulated in mock mode. Latest capture is Unavailable in normal mode.

Tracking starts STOPPED on every load. Start/Pause/Resume/Stop remain local UI
state. No screenshots are captured or uploaded; recovery never restarts tracking.
No capture timestamps are derived from activity segments.

## Desktop

```powershell
npm.cmd run desktop
npm.cmd run desktop:build
```

Portable Windows builds go under `release/`; `desktop:unpacked` creates an
unpacked folder. The existing sandboxed Electron renderer has no Node access or
native capture bridge. The initial executable is unsigned with default branding.

## Manual verification

Normal mode: header/tracking/date controls load; history, backend and capture
display Needs confirmation; latest capture is unavailable; network tools show no
API calls. Start → Pause → Resume → Stop stays local. Refresh returns to STOPPED.

Development mock mode: inspect history success, empty, loading, error and Retry;
pending/processing/failed captures; upload error; permission error. For permission
error, Stop, select the scenario, then Start. Stop during STARTING cancels start.
Mock connection status is labeled simulated. Check narrow widths and keyboard use.

Real reachable/offline status, timeline success/empty/error, upload and polling
cannot be verified until the contract gaps and backend routes are implemented.
Backend CORS must allow the selected frontend origin when calls become available;
keep browser security enabled. This task makes no backend CORS changes.
