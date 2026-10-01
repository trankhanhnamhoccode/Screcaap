# ADR 0003: PostgreSQL, SQLAlchemy, and Alembic

## Context

The MVP needs persistent capture metadata, processing state, derived results, and activity segments with relationships and transactional updates.

## Decision

Use PostgreSQL as the metadata and results database, SQLAlchemy 2.x for persistence mapping/repositories, and Alembic for schema migrations. Keep ORM models and queries in infrastructure; application services depend on repository abstractions. Screenshot bytes are stored outside PostgreSQL.

## Consequences

The backend gains relational constraints and migrations. Local development needs PostgreSQL. Physical tables, indexes, deletion policy, and transaction boundaries require design in `docs/database.md` and migrations before implementation.
