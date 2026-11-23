# Penciled API: deploy runbook (SPR-04)

One warm container (FastAPI + uvicorn, one process) in front of a managed Postgres.
Idempotency results live in that process's memory for 10 min (D20.2), so the beta runs
**exactly one instance**; a second instance would only cause counted re-runs
(`idem_memory_miss`), never wrong answers.

**Never put a secret value in any file, commit, issue or chat.** Every value below in
`<angle brackets>` is a placeholder you type into the host's secret store yourself.

## 0. What the server needs at runtime

| Variable | Secret? | Meaning |
|---|---|---|
| `DATABASE_URL` | **yes** | Postgres URL from the managed provider (`postgres://...` is accepted). |
| `PENCILED_MIN_APP_VERSION` | no | 426 below this; default `0.1.0` (set in `fly.toml [env]`). |
| `PENCILED_PAUSED` | no | `1` = global kill switch, every extract returns `503 {basic:true}`. |
| `PENCILED_GLOBAL_DAILY_USD_CAP` | no | Global daily $ estimate cap; default `1.0`. |
| `PENCILED_TIER_LIMITS_PATH` | no | Optional override of `app/config/tier_limits.json`. |
| `PENCILED_BURST_PER_MINUTE` | no | 429 burst limit per token; default 30. |
| provider key (SPR-05) | **yes** | Not used yet; will be added with `fly secrets set` the same way. |

## 1. Option A (recommended): Fly.io

1. Create a Fly.io account (builder action; a card may be required **verify**) and install
   `flyctl` (`winget install flyio.flyctl` or the PowerShell installer on fly.io/docs).
2. `fly auth login`
3. Create the app without deploying (from the repo root):
   `fly launch --no-deploy --copy-config --config server/fly.toml --name <app-name>`
   then set `app = "<app-name>"` and `primary_region` in `server/fly.toml`.
4. Managed Postgres, free or low tier. Pick one and create a database in a region next to
   the app (**verify current free tiers**):
   - Fly Managed Postgres (`fly mpg create`), or
   - Neon / Supabase free tier (copy the pooled or direct connection string, `sslmode=require`).
   Record the backup retention of the chosen plan for SP-6 (D20.2: no content is ever stored,
   so backups hold hashes and counts only).
5. Set the secret (typed by you; never echo it into a file or a shell history you share):
   `fly secrets set DATABASE_URL=<postgres-url> --config server/fly.toml`
6. Deploy (the release command runs `alembic upgrade head` first):
   `fly deploy --config server/fly.toml --dockerfile server/Dockerfile .`
   (**verify**: flyctl resolves `[build] dockerfile` relative to the config file; the
   explicit `--dockerfile` flag and the trailing `.` keep the repo root as build context.)
7. Keep exactly one warm machine: `fly scale count 1 --config server/fly.toml`.
   `fly.toml` already sets `auto_stop_machines = "off"` and `min_machines_running = 1`.
8. Verify:
   - `curl https://<app-name>.fly.dev/v1/health` returns `{"status":"ok","schema_version":1}`
   - `fly logs --config server/fly.toml` shows JSON lines with route/status/latency only.
9. Issue tester invites (one per tester; the code is printed once, only its hash is stored):
   `fly ssh console --config server/fly.toml -C "python -m app.admin add-invite"`
   Revoke: `... -C "python -m app.admin revoke-invite <code>"`.

Body logging: Fly's proxy does not log request bodies; the app logs none (uvicorn access
log disabled, scrubbing formatter on every line). Do not add a log shipper that captures
bodies.

## 2. Option B: Google Cloud Run (notes)

- Build and push: `gcloud builds submit --tag <region>-docker.pkg.dev/<project>/<repo>/penciled-api -f server/Dockerfile .`
  (or `docker build -f server/Dockerfile .` in CI and push).
- Secret: `printf '%s' '<postgres-url>' | gcloud secrets create penciled-database-url --data-file=-`
  (type the value yourself; never commit it).
- Deploy one warm instance, no scale-to-zero:
  `gcloud run deploy penciled-api --image <image> --region <region> --port 8080 --min-instances=1 --max-instances=1 --no-cpu-throttling --set-secrets DATABASE_URL=penciled-database-url:latest --allow-unauthenticated`
- Migrations: a Cloud Run job with the same image and secret, command `alembic upgrade head`,
  run before each deploy that adds a migration.
- Cloud Run request logs carry URL, status and latency, not bodies. Do not enable any
  request/response body logging (Cloud Armor/LB verbose logging off).
- Health: `curl https://<service-url>/v1/health`.

## 3. Rollback and kill switch

- Kill switch without a deploy: `fly secrets set PENCILED_PAUSED=1` (restarts the machine;
  every extract returns `503 {basic:true}`; clients show ST-PAUSED).
- Rollback: `fly releases` then `fly deploy --image <previous-image-ref>`.
- Migrations are forward-only in production; `alembic downgrade` is for local use.

## 4. Local run (no Docker needed)

```
cd server
# a Postgres to talk to: CI uses postgres:16; locally PGlite works (see STATUS.md)
set DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:54329/postgres   # local throwaway only
.venv/Scripts/alembic upgrade head
.venv/Scripts/python -m app.serve        # PORT defaults to 8080
curl http://127.0.0.1:8080/v1/health
```
