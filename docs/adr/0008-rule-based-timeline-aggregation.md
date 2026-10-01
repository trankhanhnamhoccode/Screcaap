# Proposal 0008: Rule-based timeline aggregation

**Status: proposed; not an agreed MVP decision.**

## Context

A screenshot is a point observation. The MVP needs a timeline without treating unseen periods as observed activity or delegating time-based behavior judgments to an LLM.

## Proposed decision

Use a deterministic rule-based aggregator. Order observations by `captured_at` before processing. Merge adjacent observations only when normalized activity/category is compatible and their time gap is below a configured maximum merge gap. Leave larger missing intervals uncertain rather than attributing them to the previous capture. `ActivitySegment` is the resulting interval concept.

## Consequences

The rule is understandable and testable without external providers. Normalization rules, the exact maximum merge gap, confidence handling, segment boundaries, recomputation strategy, and representation of uncertain intervals remain TODO.
