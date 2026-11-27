# AGENTS.md

Guidance for AI coding agents in `ecommerce-saas`. Code and config are the source of
truth; `README.md` documents endpoints, but its "Next Steps" section is stale.

## Shape of the repo

- Two independent apps: `backend/` (FastAPI, Python 3.13, uv, Supabase PostgreSQL via
  async SQLAlchemy + asyncpg, Alembic) and `frontend/` (React 19 + TypeScript + Vite,
  npm, plain CSS). No shared package or workspace root manifest.
- `backend/app/main.py` mounts routers under `/api` and serves both `/health` and
  `/api/v1/health`. Route handlers in `app/api/` are thin; rules live in
  `app/services/*`. Get sessions only from `get_db` in `app/db/session.py`; the engine
  is disposed in the app lifespan.
- Every product, customer, order, and analytics query is filtered by the authenticated
  user's `owner_id`; a missing record or someone else's record is a `404`. Money is
  `Decimal`, never `float`.
- Order creation validates the customer and products for the current owner, merges
  duplicate lines, stores `price_at_time_of_purchase`, and checks/deducts stock in one
  transaction; insufficient stock is `409`. Analytics revenue counts only completed
  orders.
- Frontend uses state-based views with hash routes (`#/login`, `#/register`,
  `#/dashboard`) — no router or HTTP client library. `src/lib/auth.ts` owns
  `requestJson`, `ApiError`, and token storage (localStorage with in-memory fallback);
  protected calls live in `lib/{products,customers,orders,analytics}.ts`. Use those
  helpers instead of raw `fetch`/`localStorage`; a `401` clears the token and returns
  to Login.

## Setup gotchas

- Copy `backend/.env.example` to `backend/.env` and `frontend/.env.example` to
  `frontend/.env`. `JWT_SECRET_KEY` is required (`openssl rand -hex 32`), and settings
  load `.env` relative to the current directory — run backend commands from `backend/`
  or imports and tests fail with a Pydantic validation error.
- Supabase: use `postgresql+asyncpg://` and percent-encode the password. `DB_SSL=true`
  is the default; the transaction pooler on port 6543 needs
  `DB_DISABLE_PREPARED_STATEMENTS=true`. Keep `DB_POOL_SIZE`/`DB_MAX_OVERFLOW` small.
- The API origin is baked into the Vite build via `VITE_API_URL` (falls back to
  `http://localhost:8000`), so rebuild after changing it, including in Docker.
  Compose reads `backend/.env` for the backend container.
- Railway is the current deploy target: two Docker services in one project,
  `e-commerce-order-manangement-saas-api` (root `backend`, detected Dockerfile,
  health `/health`, binds `$PORT`) and `e-commerce-order-manangement-saas-web`
  (root `frontend`, detected Dockerfile, nginx binds `$PORT`). `VITE_API_URL` is a
  build-time variable on the web service; API `CORS_ORIGINS` must name the exact
  web hostname. See `DEPLOYMENT.md`. `render.yaml` is historical and superseded;
  Alembic migrations must be applied to Supabase manually.
- Confirm with the user before adding major dependencies or architectural patterns
  beyond this stack.

## Commands (verified)

From `backend/`, with `.env` present:

```bash
uv sync
uv run uvicorn app.main:app --reload --port 8000
uv run pytest -q                      # currently 68 passed, 1 skipped
uv run pytest tests/test_orders.py -q # single file
RUN_DB_TESTS=1 uv run pytest tests/test_database.py -v   # live Postgres required
uv run ruff check .
uv run mypy app
uv run alembic revision --autogenerate -m "description"
uv run alembic upgrade head
```

From `frontend/`: `npm install`, `npm run dev`, `npm run lint`, `npm run build`.
From the repo root: `docker compose up --build`, `docker compose down`.

## Testing quirks

- `tests/conftest.py` overrides `get_db` with a fresh in-memory SQLite database
  (`aiosqlite` + `StaticPool`) per test, using `httpx.AsyncClient`/`ASGITransport` and
  `anyio_backend = asyncio`. Import new ORM models in `app/models/__init__.py` so
  `Base.metadata.create_all` creates their tables.
- `test_database.py` is skipped unless `RUN_DB_TESTS=1`; it uses the real Supabase
  connection. The default suite needs no running database.

## Conventions

- Validate and authorize on the server; never trust client prices, totals, or owner
  IDs. Avoid leaking internal exception text in error responses.
- Keep Ruff's 100-character line length; use async database access only through
  `get_db`.
- Never commit `.env` files, secrets, `dist/`, `.venv`, or caches.
