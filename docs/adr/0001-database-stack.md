# ADR-0001: Database Stack

  
## Status

Accepted

  

## Context

The project is a personal finance tracker built with FastAPI.

It needs a reliable way to work with PostgreSQL, support schema migrations,

and cleanly separate database models from API schemas.

  

Main goals when choosing the stack:

- Align with requirements commonly seen in Junior/Middle Python backend vacancies

- Use patterns familiar from previous experience with Entity Framework and DTOs in C#

- Prefer explicit separation between persistence models and API schemas

- Support asynchronous database operations

  

## Decision

We will use the following stack:

  

- **SQLAlchemy 2.x** (async mode) as the ORM

- **Alembic** for database migrations

- **Pydantic** for request/response schemas (kept separate from SQLAlchemy models)

- **asyncpg** as the PostgreSQL driver

- **PostgreSQL** as the database

  

## Consequences

  

### Positive

- Strong match with current job market requirements

- Familiar mental model (similar to Entity Framework + DTOs)

- Clear separation of concerns between database and API layers

- Full control over migrations and SQL when needed

- Mature and well-documented ecosystem

  

### Negative / Trade-offs

- More boilerplate compared to tools like SQLModel

- Need to keep SQLAlchemy models and Pydantic schemas in sync manually

- Async session handling requires careful design