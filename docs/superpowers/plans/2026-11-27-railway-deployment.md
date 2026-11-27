# Railway Two-Service Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy the FastAPI API and Vite frontend as two Railway Docker services backed by the existing Supabase database.

**Architecture:** Keep the repo's two Dockerfiles as the build units. Change only how each container picks up Railway's injected `PORT`, then configure two services in one Railway project with explicit build-time `VITE_API_URL` and runtime `CORS_ORIGINS`. Supabase stays external and migrations stay manual.

**Tech Stack:** Python 3.13, FastAPI, uv, React 19, TypeScript, Vite 8, `nginx:alpine`, Railway Free, Supabase PostgreSQL.

**Spec:** `docs/superpowers/specs/2026-11-27-railway-deployment-design.md`

## Global Constraints

- Keep the slug exactly `e-commerce-order-manangement-saas` (note "manangement") in all service names.
- Use exactly two Railway services in one project: `e-commerce-order-manangement-saas-api` and `e-commerce-order-manangement-saas-web`.
- No new dependencies, no Railway IaC/config-as-code files, no database on Railway.
- Backend commands run from `backend/` with `.env` present; frontend commands run from `frontend/`.
- API must bind Railway's injected `PORT`; local Compose must continue to work at 8000.
- Web nginx must listen on Railway's injected `PORT`; local Compose must continue to work at 80.
- `envsubst` does not support `${PORT:-80}`; the Dockerfile sets `ENV PORT=80` as the local default instead.
- `VITE_API_URL` is a build-time Vite value; changing it requires rebuilding/redeploying the web service.
- `CORS_ORIGINS` must be a JSON array with the exact deployed web origin, no wildcard and no trailing slash.
- Supabase connection uses `postgresql+asyncpg://`, percent-encoded password, `DB_SSL=true`; session pooler port 5432 with `DB_DISABLE_PREPARED_STATEMENTS=false`.
- Alembic migrations are applied manually; no deploy-time migration command.
- `render.yaml` is historical/superseded and is not deleted in this plan.
- Never commit `.env` files, secrets, `dist/`, `.venv`, or caches.

## Review Focus

- Railway injects `PORT` (commonly 8080): API must bind it or the `/health` check fails — Task 2's Dockerfile test pins `${PORT:-8000}`.
- Railway injects `PORT` into the nginx container: web must listen there or the site is unreachable — Task 3's template check pins `listen ${PORT};` and the build check proves the image still builds.
- `VITE_API_URL` is baked into the bundle: a missing value leaves `http://localhost:8000` in production JS — Task 3's build check proves the supplied value appears in `dist/`, and Task 5 verifies browser requests go to the Railway API host.
- CORS mismatch blocks login/register: API `CORS_ORIGINS` must match the exact web hostname — Task 5 sets it from the captured hostname and runs a browser request check.
- Supabase Free pauses or pooler settings are wrong: authenticated requests fail with 500s — Task 5 checks the project is active, applies migrations, and creates a product/order after deploy.

---

### Task 1: Update repo guidance for Railway

**Files:**
- Modify: `AGENTS.md:41-46`

**Interfaces:**
- Consumes: nothing.
- Produces: agent guidance that names Railway as current and `render.yaml` as historical.

- [ ] **Step 1: Replace the Render paragraph in `AGENTS.md`**

Replace lines 41–46 with a paragraph that states: Railway is the current deploy target; two Docker services in one project named `e-commerce-order-manangement-saas-api` (root `backend`, detected Dockerfile, health `/health`, binds `$PORT`) and `e-commerce-order-manangement-saas-web` (root `frontend`, detected Dockerfile, nginx binds `$PORT`); `VITE_API_URL` is a build-time variable on the web service; API `CORS_ORIGINS` must name the exact web hostname; see `DEPLOYMENT.md`; `render.yaml` is historical and superseded; Alembic migrations are applied to Supabase manually.

- [ ] **Step 2: Verify the guidance**

Run from the repo root:

```bash
grep -F 'Railway is the current deploy target' AGENTS.md
grep -F 'render.yaml is historical and superseded' AGENTS.md
```

Expected: both commands print a line; no Render setup instructions remain in that paragraph.

- [ ] **Step 3: Commit**

```bash
git add AGENTS.md && git commit -m "docs: mark Railway as current deploy target"
```

---

### Task 2: Bind the API container to Railway's PORT

**Files:**
- Modify: `backend/Dockerfile:21`
- Test: `backend/tests/test_deploy_config.py`

**Interfaces:**
- Consumes: nothing.
- Produces: API image whose default command is `uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}`.

- [ ] **Step 1: Write the failing test**

Create `backend/tests/test_deploy_config.py` with:

```python
from pathlib import Path

DOCKERFILE = Path(__file__).resolve().parents[1] / "Dockerfile"


def test_dockerfile_binds_railway_port_with_local_fallback() -> None:
    assert (
        'CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]'
        in DOCKERFILE.read_text()
    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run from `backend/`: `uv run pytest tests/test_deploy_config.py -q`
Expected: FAIL because the current CMD hardcodes port 8000.

- [ ] **Step 3: Implement the change**

In `backend/Dockerfile`, replace the final line with:

```dockerfile
CMD ["/bin/sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

Leave `EXPOSE 8000` unchanged; Compose still maps host 8000 to container 8000 when `PORT` is unset.

- [ ] **Step 4: Verify**

Run from `backend/`:

```bash
uv run pytest tests/test_deploy_config.py -q
uv run pytest -q
uv run ruff check .
uv run mypy app
```

Expected: all pass (full suite previously 68 passed, 1 skipped).

- [ ] **Step 5: Commit**

```bash
git add backend/Dockerfile backend/tests/test_deploy_config.py && git commit -m "fix: bind API container to injected PORT"
```

---

### Task 3: Bind the web container to Railway's PORT

**Files:**
- Modify: `frontend/Dockerfile:17-23`
- Create: `frontend/nginx.conf.template`

**Interfaces:**
- Consumes: nothing.
- Produces: nginx image that listens on `$PORT` (default 80 locally) and serves the Vite build with an SPA fallback.

- [ ] **Step 1: Write the failing checks**

Run from the repo root:

```bash
grep -F 'ENV PORT=80' frontend/Dockerfile
grep -F 'COPY nginx.conf.template /etc/nginx/templates/default.conf.template' frontend/Dockerfile
grep -F 'listen ${PORT};' frontend/nginx.conf.template
```

Expected: FAIL because the template and ENV line do not exist yet.

- [ ] **Step 2: Implement the Dockerfile change**

In `frontend/Dockerfile`, replace the final `FROM nginx:alpine` stage so it contains, in order: `ENV PORT=80`, the existing `COPY --from=build /app/dist /usr/share/nginx/html`, `COPY nginx.conf.template /etc/nginx/templates/default.conf.template`, `EXPOSE 80`, and the existing `CMD ["nginx", "-g", "daemon off;"]`. Do not use `${PORT:-80}` in nginx config.

- [ ] **Step 3: Create the nginx template**

Create `frontend/nginx.conf.template` with a single `server` block that listens on `${PORT}`, sets `server_name _`, serves root `/usr/share/nginx/html`, indexes `index.html`, and uses `try_files $uri $uri/ /index.html;` in `location /`.

- [ ] **Step 4: Verify the checks and build**

Run from the repo root (with `backend/.env` present, as required by Compose):

```bash
grep -F 'ENV PORT=80' frontend/Dockerfile
grep -F 'COPY nginx.conf.template /etc/nginx/templates/default.conf.template' frontend/Dockerfile
grep -F 'listen ${PORT};' frontend/nginx.conf.template
docker compose config > /dev/null
```

Then from `frontend/`:

```bash
npm run lint
VITE_API_URL=https://railway-api-placeholder.invalid npm run build
grep -R -q 'railway-api-placeholder.invalid' dist
```

Expected: all commands succeed; the last grep confirms `VITE_API_URL` is baked into the bundle.

- [ ] **Step 5: Commit**

```bash
git add frontend/Dockerfile frontend/nginx.conf.template && git commit -m "fix: bind frontend nginx to injected PORT"
```

---

### Task 4: Write the Railway deployment runbook

**Files:**
- Create: `DEPLOYMENT.md`

**Interfaces:**
- Consumes: Task 1–3 changes and the exact service names from Global Constraints.
- Produces: a human-executable checklist for Railway dashboard configuration and post-deploy verification.

- [ ] **Step 1: Write `DEPLOYMENT.md`**

Include these sections with exact values, without inventing hostnames:

1. **Overview** — Railway Free, two Docker services in one project, Supabase external, manual migrations, `render.yaml` historical/superseded.
2. **Prerequisites** — GitHub repo access; Supabase project active; session pooler URL on port 5432; `JWT_SECRET_KEY` generated with `openssl rand -hex 32`; Alembic applied with `uv run alembic upgrade head` from `backend/`.
3. **API service** — name `e-commerce-order-manangement-saas-api`, root directory `backend`, detected Dockerfile, public networking, healthcheck `/health`, and variables `DATABASE_URL`, `JWT_SECRET_KEY`, `CORS_ORIGINS`, `ENVIRONMENT=production`, `DB_SSL=true`, `DB_DISABLE_PREPARED_STATEMENTS=false`.
4. **Web service** — name `e-commerce-order-manangement-saas-web`, root directory `frontend`, detected Dockerfile, public networking, and variable `VITE_API_URL=https://<actual-api-host>` copied from step 3.
5. **Finalize CORS** — after web hostname exists, set API `CORS_ORIGINS=["https://<actual-web-host>"]` and redeploy API.
6. **Rebuild rule** — any `VITE_API_URL` change requires a web redeploy; any web hostname change requires an API CORS update and redeploy.
7. **Free-tier note** — $1/month shared credit, services sleep after 5–10 minutes idle, first request may be slow.
8. **Verification** — `curl -f https://<api-host>/health`; open the web URL; register/login; create a product; place an order; confirm browser network requests target the Railway API host rather than `localhost`.

- [ ] **Step 2: Verify the runbook values**

Run from the repo root:

```bash
grep -F 'e-commerce-order-manangement-saas-api' DEPLOYMENT.md
grep -F 'e-commerce-order-manangement-saas-web' DEPLOYMENT.md
grep -F 'CORS_ORIGINS=["https://<actual-web-host>"]' DEPLOYMENT.md
grep -F 'curl -f https://<api-host>/health' DEPLOYMENT.md
```

Expected: all four commands print a matching line.

- [ ] **Step 3: Commit**

```bash
git add DEPLOYMENT.md && git commit -m "docs: add Railway deployment runbook"
```

---

### Task 5: Apply the Railway configuration and verify production

**Files:** none — dashboard and live checks only.

**Interfaces:**
- Consumes: `DEPLOYMENT.md` and the deployed images from Tasks 2–3.
- Produces: a live API at the captured Railway API host and a live web app at the captured Railway web host.

- [ ] **Step 1: Create the API service**

In a new Railway project, add a service from the GitHub repo with root directory `backend`, accept the detected `backend/Dockerfile`, enable public networking, set healthcheck path to `/health`, and add the variables listed in `DEPLOYMENT.md`. Record the generated public hostname in your deployment notes for the next steps.

- [ ] **Step 2: Create the web service**

Add a second service from the same repo with root directory `frontend`, accept the detected `frontend/Dockerfile`, enable public networking, and set `VITE_API_URL=https://<actual-api-host>` using the hostname from Step 1. Wait for the deploy to finish and copy the web hostname.

- [ ] **Step 3: Finalize CORS and redeploy the API**

Set the API variable `CORS_ORIGINS` to `["https://<actual-web-host>"]` and redeploy the API service. Confirm no wildcard or trailing slash is present.

- [ ] **Step 4: Apply migrations and verify the database**

From `backend/` with `.env` pointing at the same Supabase database:

```bash
uv run alembic upgrade head
uv run pytest -q
```

Expected: migration succeeds; tests pass. Also confirm in Supabase dashboard that the project is not paused.

- [ ] **Step 5: Verify the live deployment**

Run:

```bash
curl -f https://<actual-api-host>/health
```

Then in the browser: open the web URL, register/login, create a product, and place an order. Open developer tools Network tab and confirm API requests go to `https://<actual-api-host>` and return 2xx.

Expected: health returns 200; all user flows succeed; no CORS errors; no requests to `localhost:8000`.
