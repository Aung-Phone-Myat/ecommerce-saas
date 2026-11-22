# AGENTS.md

Guidance for AI coding agents working in this repository.

## Project Overview

`ecommerce-saas` is an ecommerce SaaS order management application with a
React + TypeScript frontend and a Python + FastAPI backend. The backend is
scaffolded and connects to Supabase PostgreSQL through async SQLAlchemy, with
Alembic migrations. Registration, JWT login, a protected `/api/users/me` route,
owner-scoped product, customer, and order CRUD with stock deduction, and owner
analytics are implemented. The frontend has Login, Register, and Dashboard
pages; the Dashboard shows an Overview with stat cards and uses tabs to manage
products, customers, and orders.

## Current State

- `backend/` — FastAPI app, settings, async SQLAlchemy session manager, and
  pytest tests.
- `frontend/` — React + Vite app with Login, Register, and a Dashboard with an
  Overview and Products/Customers/Orders tabs; plain CSS.
- `README.md` — setup and run instructions, including Docker Compose.
- `docker-compose.yml` — runs the backend and frontend containers together.
- `.gitignore`, `LICENSE`, `AGENTS.md`.
- `User`, `Product`, `Customer`, `Order`, and `OrderItem` models, Alembic
  migrations, registration, JWT login, protected `/api/products` and
  `/api/customers` CRUD, protected `/api/orders` creation/listing/status
  updates, and a protected `/api/analytics/summary` endpoint. The Dashboard
  shows an Overview with stat cards and manages products, customers, and orders.

Confirm with the user before introducing major dependencies or architectural
patterns beyond the stack below.

## Stack

- **Language:** Python 3.13+
- **Web framework:** FastAPI
- **Data layer:** Supabase PostgreSQL via SQLAlchemy 2.x async + asyncpg, with
  Alembic migrations
- **Backend package manager:** uv
- **Frontend:** React 19 + TypeScript + Vite, plain CSS
- **Frontend package manager:** npm
- **Tests:** pytest
- **Lint/format:** Ruff (backend), oxlint (frontend)
- **Typing:** mypy (backend), TypeScript (frontend)

When scaffolding the project, add the corresponding manifest and lockfile, and
update the Commands section below with the real commands.

## Layout

```
backend/
  app/
    main.py          # FastAPI application factory and lifespan wiring
    api/auth.py      # POST /api/auth/register and /api/auth/login
    api/deps.py      # JWT bearer dependency
    api/users.py     # GET /api/users/me
    api/products.py  # Protected /api/products CRUD
    api/customers.py # Protected /api/customers CRUD
    api/orders.py    # Protected /api/orders creation, reads, status updates
    api/analytics.py # Protected /api/analytics/summary metrics
    api/v1/          # Versioned routers (health currently)
    core/config.py   # Environment-based settings, including JWT
    core/security.py # Argon2 hashing and JWT encode/decode
    db/base.py       # Declarative base
    db/session.py    # Async engine, session manager, get_db dependency
    models/user.py   # User ORM model
    models/product.py # Product ORM model (owner_id FK)
    models/customer.py # Customer ORM model (owner_id FK)
    models/order.py  # Order and OrderItem ORM models (owner_id FK)
    schemas/user.py  # Registration and public user schemas
    schemas/product.py # Product create/update/read schemas
    schemas/customer.py # Customer create/update/read schemas
    schemas/order.py # Order create/read/status schemas
    schemas/analytics.py # Owner metrics summary schema
    services/auth.py # Registration and login business logic
    services/product.py # Owner-scoped product CRUD logic
    services/customer.py # Owner-scoped customer CRUD logic
    services/order.py # Owner-scoped orders and transactional stock deduction
    services/analytics.py # Owner-scoped dashboard metrics aggregation
  tests/             # pytest tests
  migrations/        # Alembic migration scripts
  alembic.ini
  pyproject.toml
  uv.lock
  Dockerfile       # Uvicorn image using uv-managed dependencies
  .dockerignore
  .env.example
frontend/
  src/
    App.tsx          # Login/Register/Dashboard view switching and hash routing
    App.css          # Component styles
    components/      # Login, Register, Dashboard, StatCard, resource forms/tables
    lib/auth.ts      # Auth API calls, token storage, shared requestJson helper
    lib/analytics.ts # Protected analytics API calls with Bearer token
    lib/products.ts  # Protected product API calls with Bearer token
    lib/customers.ts # Protected customer API calls with Bearer token
    lib/orders.ts    # Protected order API calls with Bearer token
    index.css        # Global styles
    main.tsx         # React entry point
  Dockerfile         # Multi-stage build; Nginx serves dist/ on port 80
  .dockerignore
  .env.example       # VITE_API_URL
docker-compose.yml   # Backend on 8000, frontend on 5173 -> 80
```

Keep route handlers thin: validate with Pydantic schemas, delegate to services,
and return schemas. Put configuration in environment variables loaded via
`pydantic-settings`; never commit secrets or real credentials.

## Commands

Run from `backend/`:

```bash
# install dependencies
uv sync

# run the dev server
uv run uvicorn app.main:app --reload --port 8000

# run tests (database test is skipped by default)
uv run pytest

# run the PostgreSQL integration test (requires DATABASE_URL)
RUN_DB_TESTS=1 uv run pytest tests/test_database.py -v

# lint / format
uv run ruff check .

# type-check
uv run mypy app

# database migrations
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

Run from `frontend/`:

```bash
# install dependencies
npm install

# run the dev server
npm run dev

# lint and build
npm run lint
npm run build
```

Do not add commands to this file that have not been verified to work.

## Conventions

- Follow PEP 8 and keep formatting consistent with Ruff defaults.
- Use type hints on public functions and FastAPI dependencies.
- Prefer small, focused modules over large files.
- Use async route handlers and async database access consistently; do not mix
  sync and async data access without a clear reason.
- Obtain database sessions through the `get_db` dependency. Do not create
  engines or sessions per request.
- Supabase requires TLS (`DB_SSL=true`). For the transaction pooler on port
  6543, also set `DB_DISABLE_PREPARED_STATEMENTS=true`.
- Handle money as integer minor units or `Decimal`, never `float`.
- Validate and authorize on the server; never trust client-supplied prices,
  totals, or ownership identifiers.
- Always scope product, customer, order, and analytics queries by the
  authenticated user's `owner_id`; return `404` for missing records and for
  records owned by another user.
- Validate order customers and products against the current owner before
  writing. Aggregate duplicate order lines, capture product prices at purchase
  time, and perform stock checks/deductions in one transaction; return `409`
  for insufficient stock.
- Return consistent error responses and avoid leaking internal exception text.
- Frontend API calls use the shared `requestJson` helper in
  `frontend/src/lib/auth.ts`; auth calls live there, protected product calls in
  `frontend/src/lib/products.ts`, protected customer calls in
  `frontend/src/lib/customers.ts`, protected order calls in
  `frontend/src/lib/orders.ts`, and analytics calls in
  `frontend/src/lib/analytics.ts`. Use `import.meta.env.VITE_API_URL` with a
  `http://localhost:8000` fallback.
- Keep the access token in the storage helper rather than accessing
  `localStorage` directly. Clear it and return to Login on any 401.
- Avoid adding a frontend router or HTTP client unless requested; the app uses
  state-based views with hash routes (`#/login`, `#/register`, `#/dashboard`).
- Add or update tests for behavior changes.

## Testing

- Use pytest with FastAPI's `TestClient` or an async client for API tests.
- Prefer isolated tests with a transactional or disposable test database.
- Database integration tests are opt-in with `RUN_DB_TESTS=1` so the default
  suite does not require a live database.
- Cover success paths, validation failures, authorization boundaries, and
  payment/order edge cases.

## Git Practices

- Keep commits focused and use clear imperative messages.
- Do not commit `.env` files, secrets, generated artifacts, or local databases.
- Do not rewrite or discard existing user work; inspect changes before
  modifying or deleting files.

## Maintaining This File

Update `AGENTS.md` whenever the stack, layout, or commands change. It should
describe the repository as it actually is, not as it is planned to be.
