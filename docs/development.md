# Development conventions

## Running the backend

TODO: Choose the runtime framework, dependencies, and a startup command. `server/main.py` is a module placeholder, not a running API. `requirements.txt` currently has no runtime packages. Do not present a command as working until the backend can actually start.

## Environment variables

Document each required variable in `.env.example` when its integration is implemented. Keep real credentials in local `.env` files, which are ignored by Git. Do not commit secrets. Variable names, defaults, and validation are TODO.

## Code and tests

- Keep API route modules in `server/api/routes/`, request wiring in `server/api/dependencies.py`, orchestration in `server/services/`, and worker entry points in `server/workers/`.
- Keep domain concepts in `server/domain/`, transport schemas in `shared/schemas/`, database models in `server/database/models/`, and persistence implementations in `server/database/repositories/`.
- Put future tests under `tests/`, mirroring `server/` and `shared/` where useful. Test behavior and boundaries rather than placeholder scaffolding.
- Follow **API → Services → Domain / Repository / OCR / LLM / Storage abstractions**. API routes must never call providers, ORM operations, or filesystem operations directly.

## Extending the backend

- **New provider:** Define or refine the interface in the relevant `base.py`, implement the adapter in its module, wire it at the composition boundary, and test it through the interface. Keep credentials and network behavior in the adapter.
- **New API route:** Add a route module or endpoint under `server/api/routes/`, use `server/api/dependencies.py` to obtain a service, and keep orchestration in that service. Update `docs/api-contract.md` with the responsible teammate.
- **New repository:** Define the needed repository abstraction in `server/database/repositories/`, keep ORM and session operations in the persistence adapter, and inject it into services. Coordinate schema decisions with the database owner.
- **Architecture changes:** Update `docs/architecture.md` and add an ADR for material changes, including context, decision, and consequences. Update related contracts and conventions in the same change.
