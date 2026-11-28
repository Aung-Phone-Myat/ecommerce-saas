# Delete customers/products used in orders — design

## Intent

Deleting a customer or product after creating an order currently returns 500 in
production: both foreign keys are `ON DELETE RESTRICT`, and the service layer
does not handle the resulting `IntegrityError`. The user wants deletion to work
without destroying order history.

## Goals

- `DELETE /api/customers/{id}` and `DELETE /api/products/{id}` return 204 even
  when the record is referenced by an order.
- Existing orders remain readable with their original customer/product details.
- While a parent still exists, order responses keep today's behavior of showing
  its current data (notably `product.price`, asserted in `tests/test_orders.py`).
- Tests enforce SQLite foreign keys so this class of bug cannot hide again.

## Non-goals / anti-goals

- No cascade deletion of orders or order items.
- No soft-delete flags or new dependencies.
- No change to owner scoping, money handling, or order totals.
- No automated Supabase migration; migrations remain a manual deploy step.

## Constraints

- FastAPI + async SQLAlchemy + Supabase Postgres; Alembic migrations applied
  manually.
- Money stays `Decimal`; Ruff line length 100; all queries owner-scoped.
- Vite build bakes `VITE_API_URL`; frontend types must match API responses.

## Approaches considered

1. **Nullable FK + `ON DELETE SET NULL` + snapshots (chosen).** DB enforces
   integrity, deletion works, history survives via captured fields.
2. **Block deletion with a 409.** Minimal, but does not meet the stated goal.
3. **Soft delete.** Hides records but needs migration plus query/UI churn.
4. **Always use snapshots in order responses.** Rejected: would change existing
   live-price behavior asserted by `test_order_keeps_price_at_time_of_purchase`.

## Decisions

- Order reads prefer the live relationship and fall back to snapshot columns
  when the parent is gone.
- Snapshots live on `orders` (`customer_name`, `customer_email`,
  `customer_phone`, `customer_address`) and `order_items` (`product_name`,
  `product_description`, `product_price`, `product_stock_quantity`).
- Alembic adds columns nullable, backfills from existing parents, then sets
  required columns NOT NULL and replaces the two RESTRICT FKs with SET NULL.
- API response ids become nullable; frontend parsers accept `null`.
- Test SQLite connections enable `PRAGMA foreign_keys=ON`.
