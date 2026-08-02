# Finance Tracker [WIP]

Personal finance tracker API (and future web UI) for managing categories and transactions with multi-user support, JWT auth, and a demo/test account.

> **Status:** active development. Backend core is largely in place; tests, stats, Dockerized API, and frontend are still ahead.

## Stack

- **API:** FastAPI
- **ORM / migrations:** SQLAlchemy 2 (async) + Alembic
- **DB:** PostgreSQL + asyncpg
- **Schemas:** Pydantic v2
- **Auth:** JWT (OAuth2 password flow)
- **Packaging:** uv
- **Containers:** Docker Compose (PostgreSQL for now; API service planned)

## What's already working

- JWT authentication (`POST /auth/login`, `GET /users/me`)
- Users are created manually in the DB (no public registration — by design, fixed small user set)
- **Categories** full CRUD with ownership checks
- **Transactions** full CRUD with ownership checks and category validation
- Nested read models (transaction → user/category)
- **Test user** (`role=test`) creation limits:
  - max 5 categories
  - max 15 transactions
- Test user **seed & reset** script (2 categories + 6 demo transactions)
- Architecture Decision Records in `docs/adr/`

## Planned

- Proper test suite (pytest + isolated test DB)
- Stats / aggregations endpoints
- Login rate limiting and extra hardening
- Refresh tokens + logout
- Backend service in Docker Compose + scheduled test-user reset (Ofelia/cron)
- Frontend
- CI/CD
- Final documentation polish

## Project layout

```text
finance-tracker/
├── backend/
│   ├── app/           # FastAPI app (api, core, models, schemas, services)
│   ├── scripts/       # operational scripts (e.g. test user reset)
│   ├── tests/         # tests (to be expanded)
│   ├── alembic/       # migrations
│   └── pyproject.toml
├── frontend/          # placeholder for future UI
├── docs/adr/          # architecture decisions
├── docker-compose.yml # PostgreSQL
└── .env.example
```

## Local setup (backend)

### 1. Clone & env

```bash
git clone https://github.com/KpeoH/finance-tracker.git
cd finance-tracker
cp .env.example .env
# edit .env: POSTGRES_* , DATABASE_URL, SECRET_KEY, etc.
```

Generate a solid `SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

### 2. Database

```bash
docker compose up -d
```

### 3. Backend

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Create users

Users are **not** registered via API. Create them in the DB (e.g. DBeaver).

Hash a password:

```bash
cd backend
uv run python -c "from app.core.security import hash_password; print(hash_password('your-password'))"
```

Insert into `users` (`name`, `password_hash`, `role`). Roles in use: `admin`, `user`, `test`.

### 5. Reset demo data (test user)

```bash
cd backend
uv run python scripts/reset_test_user.py
```

Finds the user with `role=test`, clears their categories/transactions, and seeds demo data. Intended to run daily at 02:00 once the API is deployed in Docker.

## API overview (current)

| Area | Endpoints |
|------|-----------|
| Auth | `POST /auth/login` |
| Users | `GET /users/me` |
| Categories | `GET/POST /categories`, `GET/PATCH/DELETE /categories/{id}` |
| Transactions | `GET/POST /transactions`, `GET/PATCH/DELETE /transactions/{id}` |
| Health | `GET /health` |

All category/transaction routes require a Bearer token and enforce ownership.

## License

MIT
