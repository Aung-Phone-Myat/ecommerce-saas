# Render Blueprint Design

Approved 2026-11-27. Small change: one new root-level `render.yaml`; no application
code changes.

## Intent

Make the app deployable to Render from Git with one reviewable file instead of manual
dashboard setup.

## Goals / non-goals

- Goal: define the backend web service, frontend static site, and their wiring.
- Goal: keep secrets out of Git and make the health check usable by Render.
- Non-goal: provisioning a database (the app uses external Supabase PostgreSQL).
- Non-goal: automatic migrations (Render's `preDeployCommand` requires a paid plan).

## Constraints / decisions

- Backend: `runtime: docker`, `rootDir: backend`, `dockerCommand` binds `$PORT`,
  `healthCheckPath: /health`, `plan: free`. `DATABASE_URL` and `JWT_SECRET_KEY` use
  `sync: false` so Render prompts for them on first sync. `CORS_ORIGINS` is the exact
  frontend origin as a JSON list. `DB_SSL=true`;
  `DB_DISABLE_PREPARED_STATEMENTS=false` for the session pooler.
- Frontend: `runtime: static`, `rootDir: frontend`, `npm ci && npm run build`,
  `staticPublishPath: dist`, build-time `VITE_API_URL` pointing at the backend's
  public URL, `NODE_VERSION=22`. Hash routing needs no SPA rewrite.
- Service names are `e-commerce-order-manangement-saas-api` and `e-commerce-order-manangement-saas-web`; changing them
  requires updating both the API URL and CORS value.
- Migrations are run once from the developer machine with the production
  `DATABASE_URL`.

## Approaches considered

- Dashboard-only: fastest first deploy, but config lives outside the repo.
- Blueprint (chosen): both services and env wiring in Git, reviewable and repeatable.
