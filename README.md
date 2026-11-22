# Ecommerce SaaS

An order management application built with a React + TypeScript frontend, a
Python + FastAPI backend, and Supabase PostgreSQL.

> **Status:** registration, JWT login, a protected `/api/users/me` route,
> owner-scoped product and customer CRUD, transactional order creation with
> stock deduction, owner analytics, Alembic migrations, and the frontend auth,
> management, and overview pages are implemented. Payment features are not.

## Tech Stack

| Layer     | Technology                          |
| --------- | ----------------------------------- |
| Frontend  | React 19, TypeScript, Vite          |
| Backend   | Python 3.13, FastAPI, Uvicorn       |
| Database  | Supabase PostgreSQL (`users`, `products`, `customers`, `orders`, `order_items`) |
| Tooling   | uv, pytest, Ruff, mypy, oxlint      |

## Repository Structure

```
ecommerce-saas/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app factory and CORS setup
│   │   ├── core/
│   │   │   ├── config.py        # Environment-based settings and JWT config
│   │   │   └── security.py      # Argon2 hashing and JWT encode/decode
│   │   ├── db/
│   │   │   ├── base.py          # Declarative base
│   │   │   └── session.py       # Async engine, sessions, get_db
│   │   ├── models/
│   │   │   ├── user.py          # User ORM model
│   │   │   ├── product.py       # Product ORM model (owner_id FK)
│   │   │   ├── customer.py      # Customer ORM model (owner_id FK)
│   │   │   └── order.py         # Order and OrderItem ORM models
│   │   ├── schemas/
│   │   │   ├── user.py          # Auth and user response schemas
│   │   │   ├── product.py       # Product create/update/read schemas
│   │   │   ├── customer.py      # Customer create/update/read schemas
│   │   │   ├── order.py         # Order create/read/status schemas
│   │   │   └── analytics.py     # Owner metrics summary schema
│   │   ├── services/
│   │   │   ├── auth.py          # Registration and login business logic
│   │   │   ├── product.py       # Owner-scoped product CRUD logic
│   │   │   ├── customer.py      # Owner-scoped customer CRUD logic
│   │   │   ├── order.py         # Owner-scoped orders and stock deduction
│   │   │   └── analytics.py     # Owner-scoped metrics aggregation
│   │   ├── api/auth.py          # POST /api/auth/register and /api/auth/login
│   │   ├── api/deps.py          # JWT bearer dependency
│   │   ├── api/users.py         # GET /api/users/me
│   │   ├── api/products.py      # Protected /api/products CRUD
│   │   ├── api/customers.py     # Protected /api/customers CRUD
│   │   ├── api/orders.py        # Protected order creation/reads/status
│   │   ├── api/analytics.py     # GET /api/analytics/summary
│   │   └── api/v1/
│   │       ├── router.py        # Versioned API router
│   │       └── health.py        # GET /api/v1/health
│   ├── tests/                   # pytest tests
│   ├── migrations/              # Alembic migrations
│   ├── alembic.ini              # Alembic configuration
│   ├── pyproject.toml           # Dependencies and tool config
│   ├── uv.lock                  # Locked backend dependencies
│   ├── Dockerfile               # Production API image
│   ├── .dockerignore
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Auth view switching and hash routes
│   │   ├── components/          # Login, Register, Dashboard, resource forms/tables
│   │   ├── lib/auth.ts          # API calls and token storage
│   │   ├── lib/products.ts      # Protected product API calls
│   │   ├── lib/customers.ts     # Protected customer API calls
│   │   ├── lib/orders.ts        # Protected order API calls
│   │   ├── lib/analytics.ts     # Protected analytics API calls
│   │   └── main.tsx             # React entry point
│   ├── package.json
│   ├── package-lock.json
│   ├── Dockerfile               # Multi-stage build with Nginx runtime
│   ├── .dockerignore
│   └── .env.example
├── docker-compose.yml           # Runs backend + frontend together
├── AGENTS.md                    # Guidance for AI agents
└── README.md
```

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) (`brew install uv`)
- Node.js 20+ and npm

## Backend

```bash
cd backend
cp .env.example .env
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Configure the database in `backend/.env` using the connection string from
Supabase Dashboard → **Connect**:

```dotenv
# Session pooler (port 5432) — recommended for a persistent backend on IPv4
DATABASE_URL=postgresql+asyncpg://postgres.[PROJECT-REF]:[YOUR-PASSWORD]@[POOLER-HOST]:5432/postgres
DB_SSL=true
DB_DISABLE_PREPARED_STATEMENTS=false
```

- Change `postgresql://` to `postgresql+asyncpg://`.
- Percent-encode reserved characters in the database password.
- Use the transaction pooler (port 6543) only for serverless deployments, and
  set `DB_DISABLE_PREPARED_STATEMENTS=true` when you do.
- Keep `DB_POOL_SIZE` and `DB_MAX_OVERFLOW` small when going through Supabase's
  shared pooler.

JWT settings in `backend/.env`:

```dotenv
# Generate with: openssl rand -hex 32
JWT_SECRET_KEY=replace-with-a-random-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Auth endpoints:

- `POST /api/auth/register`
- `POST /api/auth/login` with either `email` or `username`, plus `password`
- `GET /api/users/me` with `Authorization: Bearer <access_token>`

Product endpoints (all require `Authorization: Bearer <access_token>`):

- `POST /api/products` — create a product owned by the current user
- `GET /api/products` — list only the current user's products
- `GET /api/products/{id}` — read one owned product
- `PUT /api/products/{id}` — partially update an owned product
- `DELETE /api/products/{id}` — delete an owned product

Prices use `Decimal` with two decimal places. Another user's product returns
`404 Product not found`.

Customer endpoints (all require `Authorization: Bearer <access_token>`):

- `POST /api/customers` — create a customer owned by the current user
- `GET /api/customers` — list only the current user's customers
- `GET /api/customers/{id}` — read one owned customer
- `PUT /api/customers/{id}` — partially update an owned customer
- `DELETE /api/customers/{id}` — delete an owned customer

Name is required; email, phone, and address are optional and can be cleared by
sending `null` in an update. Another user's customer returns
`404 Customer not found`.

Order endpoints (all require `Authorization: Bearer <access_token>`):

- `POST /api/orders` — place an order for one of the current user's customers
- `GET /api/orders` — list only the current user's orders
- `GET /api/orders/{id}` — read one owned order with customer and product details
- `PUT /api/orders/{id}/status` — update an owned order's status

Create an order with:

```json
{
  "customer_id": 1,
  "items": [
    { "product_id": 1, "quantity": 2 },
    { "product_id": 2, "quantity": 1 }
  ]
}
```

The customer and every product must belong to the current user. Duplicate
product lines are combined. The server captures each product's current price in
`price_at_time_of_purchase`, calculates `total_amount`, and deducts stock in the
same transaction. Allowed statuses are `pending`, `paid`, `shipped`,
`completed`, and `cancelled`. Foreign resources return `404`, and insufficient
stock returns `409` with no stock changes.

Analytics endpoint (requires `Authorization: Bearer <access_token>`):

- `GET /api/analytics/summary` — return dashboard metrics for the current user

The response contains `total_products`, `total_customers`, `total_orders`,
`total_revenue` (sum of `total_amount` for completed orders), and
`pending_orders`. Every value is scoped to the authenticated user.

- API docs: <http://localhost:8000/docs>
- Health check: <http://localhost:8000/health>
- Versioned health check: <http://localhost:8000/api/v1/health>

Run the backend checks:

```bash
uv run pytest
uv run ruff check .
uv run mypy app

# Requires a reachable database configured in .env
RUN_DB_TESTS=1 uv run pytest tests/test_database.py -v

# Apply database migrations to Supabase
uv run alembic upgrade head
```

## Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

- App: <http://localhost:5173>
- Login: <http://localhost:5173/#/login>
- Sign up: <http://localhost:5173/#/register>
- Dashboard: <http://localhost:5173/#/dashboard>

The Login page links to the Sign up page, which posts `username`, `email`, and
`password` to `/api/auth/register`. It validates that all fields are filled, the
username and password meet backend length rules, the email looks valid, and both
passwords match. Backend errors such as duplicate email are shown in the form.
After a successful signup, the UI shows “Account created successfully” and
returns to Login.

The Login page has one identifier field. Values containing `@` are sent as
`email`; everything else is sent as `username`. A successful login stores the
access token in `localStorage` and opens the Dashboard. All protected requests
use `Authorization: Bearer <token>`; a missing or invalid token clears the
stored session and returns to Login.

The Dashboard fetches `/api/users/me`, `/api/analytics/summary`, `/api/products`,
`/api/customers`, and `/api/orders`. An Overview section at the top shows stat
cards for revenue, orders, customers, products, and pending orders. Tabs switch
between Products, Customers, and Orders without a frontend router.

- **Overview:** stat cards fetched from `/api/analytics/summary`, with total
  revenue highlighted. Refreshing any resource also refreshes the overview.
- **Products:** table with name, price, and stock quantity; add/edit forms send
  name, description, price, and stock quantity.
- **Customers:** table with name, email, and phone; add/edit forms send name,
  email, phone, and address. Empty optional fields are sent as `null`.
- **Orders:** table with order ID, customer name, total, status, and date, plus
  a "Mark as Completed" action. The create form selects a customer and adds
  dynamic product rows with quantities, showing an estimated total. Successful
  creation resets the form and refreshes both orders and products (stock was
  deducted).

Products and Customers provide add, edit, and delete actions; Orders provides
create and status-update actions. All tabs have loading and error states.
Successful changes refresh or update the list immediately, and any 401 clears
the session and returns to Login.

Set the API origin in `frontend/.env`:

```dotenv
VITE_API_URL=http://localhost:8000
```

Build and lint the frontend:

```bash
npm run build
npm run lint
```

## Docker

The backend and frontend can also run together with Docker Compose as an
alternative to the two-terminal workflow below. Docker and the Compose plugin
are required. Create `backend/.env` first; Compose reads it for the database
connection, JWT secret, and CORS settings:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your Supabase URL, JWT secret, and CORS_ORIGINS.
```

Build and start both services:

```bash
docker compose up --build
```

If you use the standalone binary, the equivalent command is
`docker-compose up --build`.

- Frontend: <http://localhost:5173>
- Backend API: <http://localhost:8000>
- API docs: <http://localhost:8000/docs>

The frontend image is built with `VITE_API_URL=http://localhost:8000` by
default. Override it before building if the backend is reachable at another
origin:

```bash
VITE_API_URL=http://localhost:8001 docker compose up --build
```

Stop the stack with `docker compose down`. The database remains the external
Supabase instance configured in `backend/.env`, so apply Alembic migrations
there as usual. Rebuild with `docker compose up --build` after code changes.

## Everyday Workflow

Run the backend and frontend in two separate terminals:

```bash
# Terminal 1
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Terminal 2
cd frontend
npm run dev
```

## Troubleshooting

- **`uv: command not found`** — install it with `brew install uv`, then restart
  the terminal.
- **Port 8000 already in use** — run Uvicorn on another port, e.g.
  `--port 8001`.
- **Port 5173 already in use** — Vite will offer the next free port
  automatically; use the URL it prints.
- **CORS errors in the browser** — make sure the frontend origin
  (`http://localhost:5173`) is listed in `CORS_ORIGINS` in `backend/.env`.

## Next Steps

1. Define the first database models and Alembic migrations.
2. Implement authentication and order management features.
3. Add a readiness check that verifies database connectivity.
