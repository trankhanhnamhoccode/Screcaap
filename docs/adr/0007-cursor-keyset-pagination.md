# Proposal 0007: Cursor/keyset pagination

**Status: proposed; not an agreed MVP decision.**

## Context

Capture and timeline collections can grow as screenshots arrive. Offset pagination can shift under concurrent inserts and become expensive.

## Proposed decision

Use cursor/keyset pagination for capture and timeline collection endpoints where appropriate. Order captures by `captured_at DESC, id DESC`; a capture cursor carries enough information to resume from both values. Keep cursors opaque at the public API boundary.

## Consequences

Repository queries and indexes must support the chosen order and owner scope. Timeline segment ordering/tie-breaker, cursor encoding, filter binding, page-size limits, and behavior while segments are recomputed remain TODO.
