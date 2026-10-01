# ADR 0001: Modular monolith and background worker

## Context

Screcaap is a small student project. Capture upload must return promptly while OCR and analysis can take longer or fail. Clear boundaries are needed without a distributed service architecture.

## Decision

Build the MVP as a modular monolith with an API process and background worker in the same codebase. Organize code into API/Transport, Application/Services, Domain, and Infrastructure. API routes call services; the worker invokes application processing use cases. Domain code depends on no web framework, ORM, queue, storage SDK, OCR implementation, or LLM provider.

## Consequences

Development and debugging remain straightforward, while slow work runs outside the HTTP request. The team must enforce dependency boundaries and operate an API and worker process. There is no separate backend service boundary.
