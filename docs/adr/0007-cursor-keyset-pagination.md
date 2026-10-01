# ADR 0007: Cursor/keyset pagination

**Status: decided for capture collections; timeline pagination remains proposed.**

## Context

Capture and timeline collections can grow as screenshots arrive. Offset pagination can shift under concurrent inserts and become expensive.

## Decision

Use cursor/keyset pagination for capture collection endpoints. Order captures by `captured_at DESC, id DESC`, with `id` as the stable tie-breaker; a capture cursor carries enough information to resume from both values. Keep cursors opaque at the public API boundary; cursor encoding/wire format remains TODO. Cursor/keyset pagination for timeline collections remains proposed.

## Consequences

Repository queries and indexes must support the chosen order and owner scope. Timeline segment ordering/tie-breaker, cursor encoding, filter binding, page-size limits, and behavior while segments are recomputed remain TODO.
