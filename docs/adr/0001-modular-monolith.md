# ADR 0001: Modular monolith for the MVP

## Context

Screcaap is a student project with a very small team. Local development, debugging, and learning matter more than distributed scaling. Clear module boundaries are still useful if a worker or integration needs extraction later.

## Decision

Build the MVP as a modular monolith rather than microservices. Keep API, services, domain, repositories, and provider adapters separate inside one backend.

## Consequences

Development and debugging are simpler, and deployment can remain small. The team must enforce dependency boundaries in code review. Extraction remains possible if demonstrated needs justify it, but it is not a current goal.
