# Render Blueprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Render Blueprint that deploys the FastAPI backend and Vite frontend.

**Architecture:** One root `render.yaml` defines a Docker web service rooted at
`backend/` and a static site rooted at `frontend/`. Secrets are entered in Render;
the frontend's API URL and the API's CORS allowlist are build/runtime config.

**Tech Stack:** Render Blueprints, Docker, uv, Vite, YAML.

**Spec:** `docs/superpowers/specs/2026-11-27-render-blueprint-design.md`

## Global Constraints

- Do not put secrets in `render.yaml`; use `sync: false` for `DATABASE_URL` and
  `JWT_SECRET_KEY`.
- Service names must stay `e-commerce-order-manangement-saas-api` and `e-commerce-order-manangement-saas-web`, or both
  `VITE_API_URL` and `CORS_ORIGINS` must be updated.
- Keep `DB_SSL=true` and `DB_DISABLE_PREPARED_STATEMENTS=false` for the Supabase
  session pooler.
- No `preDeployCommand`: it requires a paid plan.

## Review Focus

- Backend bind port: must use `$PORT`, not the Dockerfile's hardcoded 8000.
- CORS: must contain the exact frontend origin with `https://` and no trailing slash.
- Build-time env: `VITE_API_URL` is compiled into the frontend bundle.
- Secret files: `.env` must remain excluded by `backend/.dockerignore`.

---

### Task 1: Create the Blueprint

**Files:**
- Create: `render.yaml`

- [ ] **Step 1: Add the backend and frontend service definitions to `render.yaml`**

Use `runtime: docker` with `rootDir: backend`, `dockerCommand` binding `$PORT`,
`healthCheckPath: /health`, and the env vars from the spec; add the static site with
`rootDir: frontend`, `npm ci && npm run build`, `staticPublishPath: dist`, and
`VITE_API_URL`/`NODE_VERSION`.

- [ ] **Step 2: Validate the file parses as YAML**

Run: `python3 -c "import yaml; yaml.safe_load(open('render.yaml'))"`
Expected: no output, exit code 0.

- [ ] **Step 3: Commit**

```bash
git add render.yaml
git commit -m "deploy: add Render Blueprint for API and frontend"
```

### Task 2: Record the new deployment surface

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: Add a short note about `render.yaml`, its two services, and the
  `render blueprints validate render.yaml` command.**

- [ ] **Step 2: Commit**

```bash
git add AGENTS.md
git commit -m "docs: note Render Blueprint deploy path"
```
