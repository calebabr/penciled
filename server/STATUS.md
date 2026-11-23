# server/STATUS.md

**State:** SPR-04 COMP-SERVER-CORE built and green locally (SQLite and Postgres via PGlite).
**Not deployed yet:** needs the builder's hosting account (see `DEPLOY.md`). Provider call
is a stub (`StubExtractor`) until SPR-05.

## SPR-04 exit checklist
- [x] pytest for each status code: 200, 202, 204, 401, 403, 413, 422, 426, 429, 500, 503
      (`tests/test_extract_statuses.py`, `test_register_auth.py`, `test_delete_me.py`).
- [x] A `tier_limits` config change changes the enforced limit; a tier set in the DB changes
      the limit; the client cannot set `tier` (`tests/test_quota.py`).
- [x] In-flight duplicate -> 202 + `retry_after` (real concurrent request, blocking fake).
- [x] `done` duplicate within 10 min served from memory, provider call count unchanged.
- [x] Text and img keys never collide (separate rows, separate cache entries, 2 provider calls).
- [x] DELETE /v1/me leaves zero rows for the token_hash in every table that has one
      (found by introspection) and purges the memory cache.
- [x] Schema check: no content column (migrated DB introspected; fragment list + allowlist;
      blob/JSON types fail; the checker's own negative test).
- [x] 422 canary: marker in neither the response nor raw (caplog) nor formatted logs; log
      capture of a full register/extract/cached/delete flow finds no body text or token.
- [x] ruff + strict mypy green; `python tools/ci/no_content_log.py` clean.
- [ ] **The server is deployed (hello).** Blocked on the builder: hosting account + managed
      Postgres + `fly secrets set DATABASE_URL=...`. Runbook: `DEPLOY.md`.

## What is here
- `app/main.py` `create_app()` factory (settings, tier limits, extractor, db, clock injectable).
- `app/api/routes.py` `/v1/health`, `/v1/register`, `/v1/extract`, `DELETE /v1/me`;
  `app/api/service.py` orchestration. Order in extract: 401 -> 413 body cap -> 422 JSON ->
  426 (before full validation, so old clients get ST-UPGRADE) -> 422 contract -> 422
  image rule (image_b64 with is_chat or !image_allowed) -> 413 text > 16 KB / image -> 429
  burst -> 503 kill switch / global $ cap -> idempotency (202 / cached 200) -> 503 daily
  cap (`basic:true`) -> provider adapter -> usage + `quota{tier,state}`.
- `app/errors.py` contract `ErrorResponse` envelopes everywhere (replaced the SPR-01
  `{"error":"invalid_request"}`); 422 issues = loc (field names / indexes only) + type.
- `app/auth/tokens.py` invite -> `pcl_` token (sha256 stored only), invite codes hashed,
  atomic invite-use counter. `python -m app.admin add-invite|revoke-invite`.
- `app/quota/service.py` + `app/config/tier_limits.json` (free 100/day, shadow 30; pro
  placeholder 100). Override path: `PENCILED_TIER_LIMITS_PATH`.
- `app/idemp/store.py` DB status rows (in_flight lease 60 s; done/failed 10 min) +
  in-process `ResultCache` (10 min TTL, bounded). Memory miss -> re-run once, counted as
  `metric_daily(idem_memory_miss, all)`.
- `app/db/schema.py` (SQLAlchemy Core) + Alembic `app/db/migrations` (`0001_initial`).
  Tables: invite, token, usage_daily, spend_daily, idempotency, metric_daily.
- `app/logs.py` scrubbing JSON formatter (templates only, never %-args; allowlisted extras;
  exception type + frames only) and an ASGI access log (method, route template, status,
  latency). `app/serve.py` runs uvicorn with its access log off, 1 worker.
- `app/proxy/adapter.py` `Extractor` protocol (seam 5) + `StubExtractor`.
- Deploy prep: `Dockerfile` (python:3.12-slim, uid 10001, build from repo root),
  `Dockerfile.dockerignore`, `fly.toml` (one warm machine, release_command migrations,
  /v1/health check), `DEPLOY.md` (Fly runbook + Cloud Run notes).

## Design choices (and deviations from DESIGN 3.4)
- SQLAlchemy 2 Core + Alembic: one metadata, dialect-portable upserts, a test asserts the
  migrations and the metadata match (`alembic check` also runs in CI).
- `token.tier` added (D25); `token.daily_limit` dropped: limits come from `tier_limits`.
- `token.invite_code` stored as `invite_hash`; separate `invite` table (hashed codes, use
  counter) so invites can be issued and revoked without code changes.
- `spend_daily(day, tier, est_micro_usd, provider_calls)` added: the global $ estimate per
  tier (D25) with no token column, so DELETE /v1/me cannot reset the global spend.
- `idempotency.key_hash = sha256(token_hash, client key)`: the raw client key is not
  stored and keys are scoped per token; created_at/updated_at kept for the sweep.
- Server-side shadow counter named `shadow_cap_hit_srv` (dim = tier) so it never sums with
  the client's `shadow_cap_hit` event.
- Daily cap = `503 service_paused {basic:true}` (beta behaviour); 429 is the per-token
  burst limit (30/min) with `Retry-After`. Provider failure = 500 `internal`, key marked
  failed so the client's automatic retry re-runs it.
- `resolve_only` makes no provider call and does not count toward the daily cap.
- Request `counters` are accepted but not stored yet (metrics sprint validates dims).

## Local commands (from `server/`)
```
python -m venv .venv && .venv/Scripts/python -m pip install -e ../shared/python -e ".[dev]"
.venv/Scripts/python -m pytest -q            # SQLite in-memory fallback
.venv/Scripts/ruff check .
.venv/Scripts/mypy app
```
Real Postgres locally without Docker (PGlite, Postgres compiled to WASM, runs on Node):
```
# in a scratch folder outside the repo
npm install @electric-sql/pglite @electric-sql/pglite-socket
npx pglite-server --port=54329 --max-connections=10
# then, in server/
set TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:54329/postgres
set PENCILED_REQUIRE_POSTGRES=1
.venv/Scripts/python -m pytest -q
```
Tests use `TEST_DATABASE_URL`, never `DATABASE_URL`, because they drop and recreate tables.
CI: the python job has a `postgres:16` service, sets `PENCILED_REQUIRE_POSTGRES=1`, runs
`alembic upgrade head / check / downgrade base`, then pytest. A `server-image` job builds the
Docker image, checks it runs as non-root and that `/v1/health` answers.

## Notes / next
- SPR-05: implement `Extractor` for COMP-LLMPROXY (provider key via `fly secrets set`),
  report real `ProviderUsage` (tokens, est_micro_usd) so the global $ cap is live.
- Single instance only in the beta (memory result cache). Redis trigger per DESIGN 4.4.
- A root `.dockerignore` (copy of `Dockerfile.dockerignore`) would also cover non-BuildKit
  builders; outside the server lane, left to the lead.
- Starlette warns that `httpx` with its TestClient is deprecated in favour of `httpx2`;
  harmless for now.
