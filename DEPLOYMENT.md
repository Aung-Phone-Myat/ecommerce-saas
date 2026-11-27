# Deployment

Railway is the current deploy target. The earlier `render.yaml` Blueprint is historical
and superseded; do not use it for this deployment.

## 1. Overview

- Railway Free runs two Docker services in one project.
- Supabase is the external PostgreSQL database; no database is created on Railway.
- Alembic migrations are applied manually, not during deploy.
- Service names keep the exact slug `e-commerce-order-manangement-saas` (note
  "manangement"):
  - `e-commerce-order-manangement-saas-api`
  - `e-commerce-order-manangement-saas-web`

## 2. Prerequisites

1. Connect this GitHub repository to Railway.
2. Confirm the Supabase project is active. Free projects pause after one week of low
   activity.
3. Get the Supabase **session pooler** connection string on port 5432, change the scheme
   to `postgresql+asyncpg://`, and percent-encode the password.
4. Generate a secret with `openssl rand -hex 32`.
5. From `backend/`, with `.env` pointing at the same Supabase database, apply migrations:

   ```bash
   uv run alembic upgrade head
   ```

## 3. API service

Create a Railway service from the repository with:

- Name: `e-commerce-order-manangement-saas-api`
- Root directory: `backend`
- Dockerfile: detected automatically at `backend/Dockerfile`
- Public networking: enabled
- Healthcheck path: `/health`

Set these service variables:

| Variable | Value |
| --- | --- |
| `DATABASE_URL` | Supabase session pooler URL from step 2 |
| `JWT_SECRET_KEY` | Secret from step 2 |
| `CORS_ORIGINS` | Temporary value is fine here; finalized in step 5 |
| `ENVIRONMENT` | `production` |
| `DB_SSL` | `true` |
| `DB_DISABLE_PREPARED_STATEMENTS` | `false` |

After the deploy finishes, copy the generated public hostname from the Railway service
settings. It is used as `<actual-api-host>` below.

## 4. Web service

Create a second Railway service from the same repository with:

- Name: `e-commerce-order-manangement-saas-web`
- Root directory: `frontend`
- Dockerfile: detected automatically at `frontend/Dockerfile`
- Public networking: enabled

Set this service variable:

| Variable | Value |
| --- | --- |
| `VITE_API_URL` | `https://<actual-api-host>` copied from step 3 |

Railway passes service variables into Dockerfile `ARG`s at build time, so this supplies
the existing `ARG VITE_API_URL` in `frontend/Dockerfile`.

After the deploy finishes, copy the generated public hostname. It is used as
`<actual-web-host>` below.

## 5. Finalize CORS

Set the API service variable `CORS_ORIGINS` to:

```text
CORS_ORIGINS=["https://<actual-web-host>"]
```

Use the exact hostname, with no wildcard and no trailing slash. Redeploy the API service
so the new value takes effect.

## 6. Rebuild rule

- Any `VITE_API_URL` change requires a web service redeploy because Vite bakes the value
  into the JavaScript bundle at build time.
- Any web hostname change requires updating API `CORS_ORIGINS` and redeploying the API.

## 7. Free-tier note

Railway Free includes $1 of usage credit per month shared by both services. Services
sleep after roughly 5–10 minutes without traffic and wake on the next request, so the
first page load or API call can be slow. There are no custom domains on Free.

## 8. Verification

1. Check the API:

   ```bash
   curl -f https://<api-host>/health
   ```

2. Open `https://<actual-web-host>` in a browser.
3. Register and log in.
4. Create a product and place an order.
5. Open browser developer tools and confirm API requests target
   `https://<api-host>` rather than `localhost:8000`, with no CORS errors.
