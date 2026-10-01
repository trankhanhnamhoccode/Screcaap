# Screcaap

Screcaap is a student project for understanding laptop activity from periodic screenshots. The backend MVP is designed as a Python modular monolith with a FastAPI API and an RQ background worker in the same codebase. Local runtime infrastructure is bootstrapped; capture processing is not implemented yet.

Start with the [product scope](docs/product.md), [architecture](docs/architecture.md), and [development conventions](docs/development.md). The [API contract](docs/api-contract.md), [conceptual data model](docs/database.md), [internal events](docs/events.md), and [ADRs](docs/adr/README.md) record decided behavior and remaining open decisions.

For Python, Docker, Compose, migration, API, and worker commands, see [local backend development](docs/development.md). The bootstrap provides `GET /health`; product endpoints are not implemented yet.
