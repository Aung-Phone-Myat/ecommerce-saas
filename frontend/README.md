# Frontend

React + TypeScript frontend for the Ecommerce SaaS application, built with Vite.

See the [root README](../README.md) for setup and run instructions.

```bash
npm install
cp .env.example .env
npm run dev
```

The app starts on the Login page and calls the FastAPI backend at
`VITE_API_URL` (default `http://localhost:8000`). Use the “Sign up” link to open
`#/register`, or log in directly. After login it stores the access token in
`localStorage` and shows the Dashboard at `#/dashboard`.

The Dashboard has Products, Customers, and Orders tabs. The Products and
Customers tabs list the current user's records and support adding, editing, and
deleting them through `/api/products` or `/api/customers`. The Orders tab lists
orders with their customer, total, status, and date; create orders with a
customer and dynamic product rows; and mark orders as completed. Creating an
order refreshes both orders and products because stock is deducted. API calls
live in `src/lib/products.ts`, `src/lib/customers.ts`, and `src/lib/orders.ts`
and always send the stored token as a bearer token.

Above the tabs, an Overview section fetches `/api/analytics/summary` and shows
`StatCard` components for total revenue (highlighted), total orders, total
customers, total products, and pending orders. Analytics calls live in
`src/lib/analytics.ts`; any successful create, update, delete, or status change
refreshes the overview.

Verify changes with:

```bash
npm run lint
npm run build
```
