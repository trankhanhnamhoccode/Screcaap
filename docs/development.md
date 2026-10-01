# Development conventions

## Running the backend

**DECIDED:** The MVP stack is Python, FastAPI, Pydantic v2, PostgreSQL, SQLAlchemy 2.x, Alembic, Redis, RQ, S3-compatible image storage with MinIO locally, pytest, and Docker Compose. See the [persistence](adr/0003-postgresql-sqlalchemy-alembic.md), [queue](adr/0004-redis-rq-background-processing.md), and [storage](adr/0005-s3-object-storage-minio.md) ADRs. This is a design decision, not an installed environment: `server/main.py` is still a placeholder, `requirements.txt` is empty, and there is no Compose file or executable startup command yet. **TODO:** Add and verify commands when implementation exists.

## Environment variables

Document each required variable in `.env.example` when its integration is implemented. Keep real credentials in local `.env` files, which are ignored by Git. Do not commit secrets. PostgreSQL, Redis, and MinIO connection variable names, defaults, and validation are **TODO**.

## Code and tests

- Keep API route modules in `server/api/routes/`, request wiring in `server/api/dependencies.py`, orchestration in `server/services/`, and worker entry points in `server/workers/`.
- Keep domain concepts in `server/domain/`, transport schemas in `shared/schemas/`, database models in `server/database/models/`, migrations in `server/database/migrations/`, and persistence implementations in `server/database/repositories/`.
- Put future tests under `tests/`, mirroring `server/` and `shared/` where useful. Test behavior and boundaries rather than placeholder scaffolding.
- Follow API and worker entry points → Services → Domain and repository/provider/storage/job abstractions. API routes must never call providers, ORM operations, object storage, or RQ directly.

## Extending the backend

- **New provider:** Define or refine the interface in the relevant `base.py`, implement the adapter in its module, wire it at the composition boundary, and test it through the interface. Keep credentials and network behavior in the adapter.
- **Background work:** Keep RQ setup and worker entry points in infrastructure. Enqueue through an application-facing scheduling boundary; the worker calls an application use case. Keep job payloads to capture identity and load current data from repositories and storage.
- **New API route:** Add a route module or endpoint under `server/api/routes/`, use `server/api/dependencies.py` to obtain a service, and keep orchestration in that service. Update `docs/api-contract.md` with the responsible teammate.
- **New repository:** Define the needed repository abstraction in `server/database/repositories/`, keep ORM and session operations in the persistence adapter, and inject it into services. Coordinate schema decisions with the database owner.
- **Architecture changes:** Update `docs/architecture.md` and add an ADR for material changes, including context, decision, and consequences. Update related contracts and conventions in the same change.

## Verification once implementation exists

Use pytest for service and domain behavior with fake repositories and providers; automated tests must not require live OpenRouter, PaddleOCR, MinIO, or paid external calls. **TODO:** Add lint/type checks when configured. Review migrations and public schema changes against [database.md](database.md) and [api-contract.md](api-contract.md).
