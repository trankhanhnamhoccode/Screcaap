# AGENTS.md

## Project

This repository contains a small student project for laptop activity tracking.

The MVP periodically captures screenshots, extracts text with OCR, interprets activity using an LLM, and builds a timeline of user activity.

Primary goals:

- understand how laptop time was spent
- identify prolonged distractions
- eventually detect behaviors such as doomscrolling or gaming longer than intended

This is both a product project and a learning project.

Prefer clear, conventional engineering over clever abstractions.

---

## Source of truth

Before making architectural changes, read:

- `docs/product.md`
- `docs/architecture.md`
- `docs/api-contract.md`
- `docs/database.md`
- `docs/events.md`
- `docs/development.md`
- relevant files under `docs/adr/`

Do not use comments or old implementation details as justification for contradicting these documents.

If implementation and documentation disagree, point out the mismatch rather than silently choosing one.

---

## Architecture

The backend is a modular monolith.

Main dependency direction:

    API
      ↓
    Services
      ↓
    Domain / Repositories / Providers

Infrastructure implementations sit behind abstractions.

Examples:

    OCRProvider
        ↓
    PaddleOCRProvider

    ActivityAnalyzer
        ↓
    OpenRouterAnalyzer

    ImageStorage
        ↓
    LocalImageStorage

API routes must not directly depend on infrastructure implementations.

---

## Layer responsibilities

### `server/api/`

HTTP-specific concerns only.

Responsibilities:

- routing
- request parsing
- response formatting
- dependency injection
- HTTP status codes

Do not place business orchestration here.

API routes must not directly call:

- PaddleOCR
- OpenRouter
- ORM queries
- filesystem operations

---

### `server/services/`

Application use cases and orchestration.

Examples:

- create capture
- request processing
- retrieve capture
- build timeline

Services may coordinate:

- repositories
- OCR providers
- LLM analyzers
- storage
- background jobs

Services should not contain framework-specific HTTP behavior.

---

### `server/domain/`

Core domain concepts and rules.

Domain code should avoid dependencies on:

- FastAPI
- SQLAlchemy
- PaddleOCR
- OpenRouter
- filesystem/storage SDKs

Important domain concepts include:

- Capture
- OCRResult
- AnalysisResult
- ActivitySegment

`ActivitySegment` is the long-term product concept.

A screenshot is primarily raw evidence used to derive activity.

---

### `server/database/`

Persistence infrastructure.

Use:

- `database/models/` for ORM models
- `database/repositories/` for persistence access
- `database/migrations/` for migrations

Do not expose ORM behavior directly to API routes.

---

### `server/ocr/`

OCR abstraction and implementations.

OCR answers:

"What text is visible?"

OCR should not decide:

"What is the user doing?"

---

### `server/llm/`

Semantic analysis abstraction and implementations.

The analyzer interprets OCR text and contextual metadata.

It may answer questions such as:

- what activity is happening?
- what general category does it belong to?
- what topic appears to be involved?

The LLM should not independently decide whether a single capture represents doomscrolling.

Behavior such as doomscrolling depends on activity over time.

---

### `server/storage/`

Image/file persistence abstractions.

Application code should depend on the storage abstraction rather than filesystem paths or cloud SDKs.

---

### `server/workers/`

Background processing entry points.

Capture processing is asynchronous by design.

Conceptual flow:

    capture.created
        ↓
    OCR
        ↓
    capture.ocr.completed
        ↓
    semantic analysis
        ↓
    capture.analysis.completed

Do not assume a specific queue technology unless an ADR explicitly selects one.

---

### `shared/schemas/`

Transport/data schemas shared between application boundaries.

Do not place ORM models here.

Do not place provider implementations here.

---

## Dependency rules

Allowed:

    api → services
    services → domain
    services → repository abstractions
    services → provider abstractions

Infrastructure may implement abstractions defined by the application/domain.

Avoid circular dependencies.

Forbidden examples:

    api → PaddleOCR
    api → OpenRouter
    api → SQLAlchemy session queries
    api → local filesystem

If a task appears to require a forbidden dependency, reconsider the design before implementing it.

---

## API principles

Prefer resource-oriented endpoints.

Prefer:

    POST /v1/captures
    GET /v1/captures/{capture_id}

Avoid action-style endpoints such as:

    /run-ocr
    /process-image
    /ask-ai

unless there is a clearly documented reason.

Capture processing is asynchronous.

`POST /v1/captures` should not wait for OCR and LLM processing to complete.

---

## Provider design

External integrations must have explicit boundaries.

Do not spread provider-specific SDK usage throughout the codebase.

Examples:

    OCRProvider
    ActivityAnalyzer
    ImageStorage

Implementations can be replaced without changing application orchestration.

---

## Database changes

Do not invent or modify the database schema casually.

Before changing persistence structure:

1. inspect `docs/database.md`
2. inspect existing migrations
3. inspect relevant repositories
4. preserve compatibility where reasonable

The detailed database design may be owned by another teammate.

If the required schema is unclear, prefer leaving a TODO or documenting the required decision instead of silently inventing a schema.

---

## API contract changes

Before modifying a public endpoint:

1. read `docs/api-contract.md`
2. preserve existing documented behavior
3. update the contract when behavior intentionally changes

Do not silently change request or response shapes.

---

## Architecture changes

Architecture changes require documentation.

For significant decisions, create an ADR under:

    docs/adr/

Use:

    Context
    Decision
    Consequences

Examples requiring an ADR:

- introducing a queue technology
- adding a major external infrastructure dependency
- introducing a new service boundary
- changing processing from asynchronous to synchronous
- changing storage strategy
- adopting microservices

---

## Avoid premature complexity

Do not introduce the following without an explicit demonstrated requirement:

- microservices
- Kubernetes
- Kafka
- event sourcing
- service discovery
- distributed tracing infrastructure
- CQRS
- unnecessary design patterns

The preferred default is the simplest implementation consistent with the documented architecture.

---

## Coding style

Prefer:

- explicit names
- small functions
- type hints
- narrow interfaces
- dependency injection
- clear module ownership

Avoid ambiguous names such as:

- `Manager`
- `Helper`
- `Utils`

unless they accurately describe the abstraction.

Avoid giant modules.

Avoid generic top-level `models/` packages.

Use the correct responsibility-specific location instead.

---

## Task workflow

Before coding:

1. read the relevant documentation
2. inspect existing implementation
3. identify the smallest change necessary
4. preserve architectural boundaries

During implementation:

1. avoid unrelated refactors
2. do not redesign nearby modules unless required
3. keep public interfaces stable unless the task explicitly changes them
4. update documentation if behavior or architecture changes

After implementation:

1. run relevant tests
2. run available lint/type checks when configured
3. check imports
4. review the diff for unrelated changes
5. summarize what changed
6. mention unresolved TODOs or assumptions

---

## Tests

New business logic should be testable without requiring real:

- OpenRouter requests
- PaddleOCR execution
- cloud storage
- external services

Prefer dependency injection and fakes/mocks at external boundaries.

Do not call paid external APIs from automated unit tests.

---

## Security and privacy

Screenshots may contain sensitive information.

Do not log:

- raw screenshot contents
- OCR text unnecessarily
- API keys
- authorization headers
- secrets
- full provider payloads containing sensitive content

Secrets belong in environment variables.

Never commit secrets.

Use `.env.example` for documented environment variable names only.

---

## When uncertain

Do not silently invent major product, API, database, or architectural decisions.

Prefer, in order:

1. existing code
2. documented project decisions
3. ADRs
4. minimal implementation consistent with existing architecture

When a meaningful decision remains unresolved, document it clearly as a TODO.