# ADR 0009: Electron desktop dashboard

## Context

The first React/TypeScript dashboard is implemented in `frontend/`. The project owner requested a desktop app. The existing Python capture client is a scaffold, and backend transport fields remain unresolved. Packaging the dashboard must not imply that capture or backend integration is complete.

## Decision

Use Electron as a thin desktop host for the existing Vite production build, with electron-builder producing a portable Windows x64 executable. Keep the React UI and plain CSS. Use relative asset paths so the same build works inside the desktop package and in the browser.

The renderer runs sandboxed with context isolation and no Node integration. No preload bridge, native capture integration, backend calls, startup registration, tray process or automatic tracking is added. Deny renderer navigation, new windows and permission requests. Closing the Windows window exits the application. Every launch starts tracking stopped.

## Consequences

The dashboard now polls the existing `/health` endpoint using a configurable build-time API URL. The local API permits GET requests from Vite development/preview origins and the file renderer's `null` origin. This checks process availability only; capture, timeline, authentication, and owner-scoped integration remain TODO pending the public contract decisions. Native capture permissions remain denied.

The desktop app reuses the web UI and runs without a Vite server or Node installation on the user's computer. Electron adds runtime/download size and desktop dependencies, but leaves the backend modular monolith unchanged. The Python client remains unchanged; its integration is a future decision.

The initial portable Windows build is unsigned and uses default executable branding. Code signing, custom installer/icon, native capture permissions, distribution/update policy and finalized owner-scoped backend contracts require follow-up before production distribution. Portable packaging is for local MVP review, not public deployment.
