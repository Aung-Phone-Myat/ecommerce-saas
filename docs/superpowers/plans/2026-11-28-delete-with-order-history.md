# Delete customers/products used in orders — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Allow deleting customers and products referenced by orders while keeping past orders fully readable.

**Architecture:** Replace the two `ON DELETE RESTRICT` foreign keys with nullable `ON DELETE SET NULL` keys, capture customer/product details on each order at creation time, and build order responses from live data with a snapshot fallback. A manual Alembic migration backfills existing orders; tests enable SQLite foreign-key enforcement so production behavior is represented.

**Tech Stack:** Python 3.13, FastAPI, async SQLAlchemy, Alembic, Supabase Postgres, SQLite/aiosqlite tests, React 19 + TypeScript + Vite.

**Spec:** `docs/superpowers/specs/2026-11-28-delete-with-order-history-design.md`

## Global Constraints

- Run backend commands from `backend/` (settings load `.env` relative to cwd).
- Never commit `.env`, secrets, `dist/`, `.venv`, or caches.
- Money is `Decimal`, never `float`. All queries remain scoped by `owner_id`.
- Keep Ruff's 100-character line length; async DB access only through `get_db`.
- No new dependencies or architectural patterns beyond the existing stack.

## Review Focus

- Delete parent referenced by an order → 204; order still readable with snapshot (`Task 1`, `Task 2`).
- Product still exists after being edited → order shows **current** product price, not snapshot (`Task 2`, existing `test_order_keeps_price_at_time_of_purchase`).
- Existing production orders have snapshots before columns become NOT NULL → migration backfill (`Task 3`).
- Frontend response parsers accept nullable ids instead of throwing "invalid order" (`Task 4`).
- Deleting another user's record still returns 404 and leaves the record intact (`Task 1`, existing parametrized access tests).

---

### Task 1: Enforce foreign keys in tests and add failing regression tests

**Files:**
- Modify: `backend/tests/conftest.py`
- Create: `backend/tests/test_delete_with_orders.py`

**Interfaces:**
- Consumes: existing API routes `/api/auth/register`, `/api/auth/login`, `/api/customers`, `/api/products`, `/api/orders`, `/api/analytics`.
- Produces: regression tests run against a FK-enforcing test database.

- [ ] **Step 1: Enable SQLite foreign keys in the test fixture**

In `tests/conftest.py`, register a SQLAlchemy `connect` event listener on the
test engine that executes `PRAGMA foreign_keys=ON` before `Base.metadata.create_all`.
Keep the existing `StaticPool` / in-memory setup unchanged.

- [ ] **Step 2: Write the three regression tests**

In `tests/test_delete_with_orders.py`, follow the local helper style of
`tests/test_orders.py` (`make_user`, `create_customer`, `create_product`,
`submit_order`). Add:

- `test_delete_customer_used_in_order_keeps_order_readable`: create customer
  `"Acme Corp"`, product `"Laptop"` at `"10.00"`, and one order; DELETE the
  customer expects 204; GET the order expects 200 with `customer_id is None`,
  `customer["id"] is None`, `customer["name"] == "Acme Corp"`, and
  `items[0]["product"]["name"] == "Laptop"`.
- `test_delete_product_used_in_order_keeps_order_readable`: create one order;
  DELETE the product expects 204; GET the order expects 200 with
  `items[0]["product_id"] is None`, `items[0]["product"]["id"] is None`,
  `items[0]["product"]["name"] == "Laptop"`, and
  `items[0]["product"]["price"] == "10.00"`.
- `test_delete_both_parents_keeps_list_status_and_analytics_working`: delete
  both parents; GET `/api/orders` expects one order; PUT
  `/api/orders/{id}/status` with `{"status": "completed"}` expects 200; GET
  `/api/analytics` expects `total_orders == 1` and `total_revenue == "10.00"`.

- [ ] **Step 3: Run the new tests and confirm they fail**

Run: `uv run pytest tests/test_delete_with_orders.py -q`
Expected: FAIL (delete endpoints return 500 / `IntegrityError`).

- [ ] **Step 4: Commit the failing tests**

```bash
git add tests/conftest.py tests/test_delete_with_orders.py
git commit -m "test: cover deleting parents referenced by orders"
```

### Task 2: Store snapshots and build resilient order responses

**Files:**
- Modify: `backend/app/models/order.py`
- Modify: `backend/app/schemas/order.py`
- Modify: `backend/app/services/order.py`
- Modify: `backend/app/api/orders.py`

**Interfaces:**
- Consumes: `Customer`, `Product`, `Order`, `OrderItem` ORM models; `OrderCreate`.
- Produces: `to_order_read(order: Order) -> OrderRead` in `app/services/order.py`;
  nullable id fields in `OrderRead`, `OrderItemRead`, `CustomerSummary`,
  `ProductSummary`.

- [ ] **Step 1: Make order FKs nullable and add snapshot columns**

In `app/models/order.py`: change `Order.customer_id` and `OrderItem.product_id`
to `Mapped[int | None]`, `nullable=True`, `ondelete="SET NULL"`. Add non-null
`customer_name: String(255)`, `customer_email: String(255) | None`,
`customer_phone: String(50) | None`, `customer_address: Text | None` to `Order`;
add non-null `product_name: String(255)`, `product_price: Numeric(12, 2)`,
`product_stock_quantity: Integer` and nullable `product_description: Text` to
`OrderItem`. Keep existing relationships, constraints, and indexes.

- [ ] **Step 2: Make response ids nullable**

In `app/schemas/order.py`, change `CustomerSummary.id`, `ProductSummary.id`,
`OrderRead.customer_id`, and `OrderItemRead.product_id` to `int | None`.

- [ ] **Step 3: Capture snapshots during order creation**

In `app/services/order.py::create_order`, load the owned customer row (not just
its id) and copy its name/email/phone/address into the new `Order` fields; copy
each product's name/description/price/stock into the corresponding `OrderItem`
fields. Do not change stock validation, totals, or transaction handling.

- [ ] **Step 4: Add `to_order_read` and use it in all order routes**

Implement `to_order_read(order: Order) -> OrderRead` in `app/services/order.py`:
build each nested summary from `order.customer` / `item.product` when present,
otherwise from the snapshot fields; keep `id` values from the FK columns. Update
`app/api/orders.py` create/list/get/status routes to call `to_order_read`
instead of `OrderRead.model_validate`. Keep `ORDER_LOAD_OPTIONS` eager loading.

- [ ] **Step 5: Run the regression and existing order tests**

Run: `uv run pytest tests/test_delete_with_orders.py tests/test_orders.py -q`
Expected: PASS, including `test_order_keeps_price_at_time_of_purchase`.

- [ ] **Step 6: Run the full backend suite and linters**

Run: `uv run pytest -q`, `uv run ruff check .`, `uv run mypy app`
Expected: all pass (one live-DB test remains skipped).

- [ ] **Step 7: Commit**

```bash
git add app/models/order.py app/schemas/order.py app/services/order.py app/api/orders.py
git commit -m "feat: preserve order history when customers or products are deleted"
```

### Task 3: Add the Alembic migration with backfill

**Files:**
- Create: `backend/migrations/versions/d4f2a1b6c9e8_allow_deleting_ordered_parents.py`

**Interfaces:**
- Consumes: current head `bcfb116290b8`; existing `orders`, `order_items`, `customers`, `products` tables.
- Produces: migration to `d4f2a1b6c9e8`, applying the schema changes of Task 2 to Supabase.

- [ ] **Step 1: Write upgrade with backfill**

Set `revision = 'd4f2a1b6c9e8'` and `down_revision = 'bcfb116290b8'`. In
`upgrade()`: add all eight snapshot columns as nullable; execute `UPDATE ...
FROM` statements filling them from joined `customers` / `products`; alter the
required columns (`customer_name`, `product_name`, `product_price`,
`product_stock_quantity`) to NOT NULL; make both FK columns nullable; drop the
existing `orders_customer_id_fkey` and `order_items_product_id_fkey` constraints
and recreate them with `ondelete='SET NULL'`.

- [ ] **Step 2: Write downgrade**

In `downgrade()`: restore the RESTRICT foreign keys and non-null FK columns,
then drop the snapshot columns. Orders with NULL parent ids block downgrade —
document that in a migration comment.

- [ ] **Step 3: Verify migration metadata**

Run: `uv run alembic heads` (expect only `d4f2a1b6c9e8`) and
`uv run alembic history` (expect the new revision after `bcfb116290b8`).
Do not apply it to Supabase from this environment.

- [ ] **Step 4: Commit**

```bash
git add migrations/versions/d4f2a1b6c9e8_allow_deleting_ordered_parents.py
git commit -m "migration: snapshot order parents and use SET NULL"
```

### Task 4: Accept nullable order ids in the frontend

**Files:**
- Modify: `frontend/src/lib/orders.ts`

**Interfaces:**
- Consumes: order API responses with nullable `customer_id`, `product_id`, and nested ids.
- Produces: TypeScript types/parsers that do not throw after a parent is deleted.

- [ ] **Step 1: Write the nullable-id parser change**

Add `readOptionalNumber(value: unknown, label: string): number | null`
(`null` passes through; otherwise reuse `readNumber`). Use it for
`OrderCustomerSummary.id`, `OrderProductSummary.id`, `OrderItemRead.product_id`,
and `Order.customer_id`, updating those interfaces to `number | null`.

- [ ] **Step 2: Verify frontend checks**

Run: `npm run lint` and `npm run build` from `frontend/`
Expected: both pass.

- [ ] **Step 3: Commit**

```bash
git add src/lib/orders.ts
git commit -m "fix: accept deleted parents in order responses"
```

### Task 5: Final verification

- [ ] **Step 1: Re-run the full checks**

From `backend/`: `uv run pytest -q`, `uv run ruff check .`, `uv run mypy app`.
From `frontend/`: `npm run lint`, `npm run build`.

- [ ] **Step 2: Reproduce the original scenario with FK enforcement**

Run the API-level reproduction (register user → customer → product → order →
delete customer and product) with `PRAGMA foreign_keys=ON`; expect 204 on both
deletes, 200 on order reads, and snapshot names in the responses.

- [ ] **Step 3: Report deploy step**

Tell the user to apply the new Alembic revision to Supabase manually and rebuild
the frontend with the intended `VITE_API_URL`.
