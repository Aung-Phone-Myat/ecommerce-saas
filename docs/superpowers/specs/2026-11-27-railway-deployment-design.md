# Railway two-service deployment design

Date: 2026-11-27

## Goal

Replace the unusable Render Blueprint with a Railway Free deployment for this repo:

- FastAPI backend runs as a Docker service built from `backend/Dockerfile`.
- React/Vite frontend runs as a second Docker service built from `frontend/Dockerfile`.
- Supabase remains the external PostgreSQL database; no database is provisioned on Railway.
- No new dependencies or architectural patterns beyond the existing stack.

## Decisions

### Hosting

| Piece | Host | Why |
| --- | --- | --- |
| API | Railway Docker service | One container, detected Dockerfile, healthcheck at `/health`. |
| Web | Railway Docker service | Same project/dashboard; nginx image kept, but must listen on Railway's injected `PORT`. |
| DB | Supabase (existing) | Session pooler, port 5432; no prepared-statement workaround needed. |
| Migrations | Manual Alembic run | Same rule as the Render plan; no deploy-time migration command. |

Both services live in one Railway project. Free plan limits: 1 project, up to 3
services, 1 vCPU / 0.5 GB RAM each, $1 usage credit per month, services sleep after
5–10 minutes idle. Two services share the same credit.

### Naming

Keep the exact slug used in the Render work: `e-commerce-order-manangement-saas`
(note the spelling "manangement"). Suggested Railway service names:

- `e-commerce-order-manangement-saas-api`
- `e-commerce-order-manangement-saas-web`

Exact public hostnames are assigned by Railway. Every CORS / API URL value must be
copied from the actual deployed `*.up.railway.app` hostnames, not guessed.

### Backend changes

- Change the container command to honor Railway's injected `PORT` while keeping local
  Compose behavior at port 8000:
  `CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`
- No application code or settings changes: `CORS_ORIGINS` already comes from the environment.
- Railway service settings:
  - Root Directory: `backend`
  - Dockerfile: detected at `backend/Dockerfile`
  - Healthcheck path: `/health`
  - Public networking enabled
  - Variables: `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `ENVIRONMENT=production`,
    `DB_SSL=true`, `DB_DISABLE_PREPARED_STATEMENTS=false`
- Use the Supabase **session pooler** (port 5432) because this is a persistent container,
  not an edge/serverless function.

### Frontend changes

- Final nginx stage gets `ENV PORT=80` as a local default. Railway overrides it with its
  injected `PORT` (commonly 8080).
- Add `frontend/nginx.conf.template` copied to
  `/etc/nginx/templates/default.conf.template`. It serves `/usr/share/nginx/html` with
  an SPA fallback and uses `listen ${PORT};`. The official nginx image runs `envsubst`
  over templates at container start.
- Do **not** write `listen ${PORT:-80};`: `envsubst` does not support shell defaults.
- Keep the existing `ARG VITE_API_URL=http://localhost:8000` in the build stage. Railway
  matches service variables to Dockerfile `ARG`s, so setting `VITE_API_URL` on the web
  service supplies it at build time.
- `VITE_API_URL` is baked into the bundle; changing it requires a web redeploy.

### CORS

Backend `CORS_ORIGINS` must be a JSON array with the exact Railway web origin, e.g.
`["https://e-commerce-order-manangement-saas-web.up.railway.app"]`. Include any custom
domain added later. No wildcard, no trailing slash.

### Deploy order

1. Create the API service; copy its public hostname.
2. Create the web service with `VITE_API_URL=https://<api-host>`.
3. Copy the web hostname; set API `CORS_ORIGINS=["https://<web-host>"]`.
4. Redeploy the API so the new CORS value takes effect.

### Render files

`render.yaml` was created for the earlier attempt and is superseded. Keep it in the
repo as historical documentation, but the deployment runbook must state that Railway
is current and Render is not used.

## Out of scope

- Custom domains.
- Railway Infrastructure-as-Code (`.railway/railway.ts`) — config-as-code is deprecated
  and IaC would add a new tool/dependency. Configuration is done in the Railway dashboard
  plus the Dockerfile/template changes.
- Automated migration on deploy.

## Verification

1. `uv run pytest -q`, `uv run ruff check .`, `uv run mypy app` from `backend/`.
2. `npm run lint`, `npm run build` from `frontend/` with a placeholder `VITE_API_URL`.
3. `docker compose config` still resolves after both Dockerfile changes.
4. After deploy: `GET /health` on the Railway API URL returns 200; the Railway web URL
   loads; register/login works; a product can be created and an order placed against
   Supabase; browser requests go to the Railway API host, not `localhost`.
