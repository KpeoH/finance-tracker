# ADR-0002: API Layer Structure (DTOs, Services and CRUD)

## Status

Accepted

## Context

The project is a personal finance tracker with a small, fixed set of users
(the owner, one family member, and a demo/test account).

We need a clear and maintainable way to structure the API layer that:

- Separates database models from request/response schemas
- Keeps business logic out of route handlers
- Enforces ownership of data (users can only access their own records)
- Follows patterns common in FastAPI projects and familiar from
  previous experience with DTOs and service-style architecture

An additional constraint is that public user registration is not required
and is intentionally omitted.

## Decision

We will use the following approach for the API layer:

- **Pydantic schemas (DTOs)** live in `app/schemas/` and are kept
  completely separate from SQLAlchemy models
- Standard schema variants are used: `Create`, `Read`, `Update`
- `Update` schemas inherit directly from `BaseSchema` and make all
  fields optional (partial update / PATCH semantics)
- Business logic and database operations live in `app/services/`
- Route handlers in `app/api/routes/` only handle HTTP concerns
  (validation, authentication, status codes, calling services)
- All mutating and read-by-id endpoints perform **ownership checks**
- Public user registration is **not** implemented. Users are created
  manually in the database. This is a deliberate decision because:
  - the application is designed for only three users
  - avoiding registration removes unnecessary complexity
  - it also avoids dealing with related legal/compliance questions

## Consequences

### Positive

- Clear separation of concerns (models / schemas / services / routes)
- Easy to test business logic in isolation
- Consistent ownership enforcement across endpoints
- Familiar structure for developers coming from DTO-based backends
- Reduced attack surface by not exposing user registration

### Negative / Trade-offs

- Some extra boilerplate when adding new entities
- Schemas and models must be kept in sync manually
- Manual user creation is less convenient than a registration endpoint
  (acceptable given the fixed and very small user base)