# server/STATUS.md

**State:** SPR-05 COMP-LLMPROXY built and green offline (contract tests against a
recorded-response fake). SPR-04 COMP-SERVER-CORE built and green (SQLite and Postgres via PGlite).
**Not deployed yet:** needs the builder's hosting account (see `DEPLOY.md`). The provider
defaults to the stub (`PENCILED_PROVIDER=stub`); `anthropic` is wired but no live call has
been made (SP-11 is builder-gated).

## SPR-05 exit checklist (COMP-LLMPROXY: AI-EXTRACT, AI-ESCALATE, SP-11)
- [x] Contract tests against a recorded-response fake: the real `anthropic` SDK over an
      `httpx2.MockTransport` replaying hand-written synthetic responses
      (`tests/fixtures/provider/*.json`, `tests/provider_fake.py`). Covered: event + related
      deadline, deadline, nothing x 5 subtypes, sensitive, unsure, refusal, malformed JSON,
      schema-invalid (extra key, 4 actions, bad kind, note > 140), truncated (max_tokens),
      ungrounded evidence, injected URL title, thinking block first, 429 + Retry-After,
      spend-cap 429, 529, 500, 400, timeout, connection error, cache write vs cache hit
      (`test_llmproxy_contract.py`, `test_llmproxy_request.py`).
- [x] 0 proxy retries (SDK `max_retries=0` forced): every failure is exactly one transport
      call; a 3-attempt client sequence is 3 calls; text -> escalate -> img is 2 calls.
- [x] Escalation only on DESIGN 5.2 triggers: never for chat, `image_allowed=false`, an img
      call, sensitive or a refusal; yes for unsure / Needs a look / missing or ungrounded
      required field / < 3 OCR lines with c >= 0.5.
- [x] Cost maths (micro-USD from config prices, cache read 0.1x, write 1.25x/2x, long-context
      card) and accounting into usage_daily / spend_daily.
- [x] No prompt / OCR / image / model text in logs (raw records and formatted output, SDK
      logger forced to WARNING even with ANTHROPIC_LOG=debug) or in any DB row
      (`test_llmproxy_privacy.py`).
- [x] SP-11 harness `tools/sp11_latency.py` (refuses without `--i-approve-spend`, prints the
      max cost first; offline tests in `test_sp11_harness.py`) and `docs/spikes/SP-11.md`
      (local, git-ignored).
- [ ] **Builder-gated:** live SP-11 run: `cache_read_input_tokens > 0` from the 2nd call,
      p50 <= 1.5 s, p95 <= 4 s, mean <= $0.002, pick an arm. Steps: `docs/spikes/SP-11.md` 6.
- [ ] **Builder-gated:** `fly secrets set ANTHROPIC_API_KEY=...` and `PENCILED_PROVIDER=anthropic`
      after SP-11 passes (and after the deploy itself).

### SPR-05 design
- `app/proxy/anthropic_extractor.py` `AnthropicExtractor` (the `Extractor` protocol): one
  `messages.create` per request; `claude-haiku-5-5`; `output_config={"effort": "low",
  "format": {"type": "json_schema", ...}}`; thinking adaptive (omitted) or `disabled` (SP-11
  arm, config); no temperature/top_p/top_k, no prefill, no tools; content read by block type.
  Refusal -> Needs a look (no escalation); max_tokens / invalid JSON / schema-invalid ->
  Needs a look (escalation allowed). `mode=resolve_only` re-shapes the echoed `raw` (itself
  re-validated) with no call.
- `app/proxy/prompts/v1/` frozen `system.txt` (6,151 chars, ~1.4-1.9K tokens, above the
  512-token Haiku 5.5 cache minimum) + `output_schema.json` (model-facing DESIGN 5.4 subset,
  plus `nothing_subtype`), pinned by sha256 in `manifest.json` (load fails on drift).
  `cache_control: {"type":"ephemeral"}` on the single system block; OCR and image after it.
- `app/proxy/request_build.py` SEC-INJ-ISOLATE: `<request_context>` (locale, chat flag) +
  `<ocr_lines>` JSON array; forged delimiters in OCR text are neutralised. The model never
  sees captured_at or tz (no date maths outside the resolver).
- `app/proxy/model_output.py` strict pydantic re-validation of the model output with the
  constraints the API cannot enforce (lengths, ranges, <= 3 actions, unknown keys rejected).
- `app/proxy/shape.py` **interim** response builder until SPR-13/14: exact (normalised)
  grounding of evidence and text values, URL/email/command titles cleared, dates always
  value null + needs_review/missing + blocking (no Ready card possible), gate `ask` or
  `needs_look`, card_score null, alarms [], notification null, deadline_origin "other",
  related_to must point at an event. SPR-14 replaces this module.
- `app/proxy/image.py` escalation preprocessing (Pillow): EXIF orientation applied then all
  metadata dropped, top 5.5% cropped (status bar), long edge <= 1,568 px, JPEG q70,
  decompression-bomb guard. Undecodable image -> 422 `image_invalid`, no call.
- `app/proxy/config.py` + `app/config/provider.json`: model, effort, thinking, max_tokens
  2048, timeout 8 s, image settings, prices. `PENCILED_PROVIDER=stub|anthropic` (default
  stub), `PENCILED_PROVIDER_CONFIG_PATH`. Key: SDK reads `ANTHROPIC_API_KEY` from the env.
- Error mapping (`app/api/service.py`): provider 429 -> our 429 with the provider's
  Retry-After; spend-cap 429 -> 503 `{basic:true}`; 529/5xx/4xx/timeout/connection -> 500
  `internal`; key marked failed so the client's next attempt re-runs.
- New precheck: `image_b64` requires the `img` key segment (422 `key_mode`), so an image
  result can never be stored under the text key.
- `usage_daily.input_tokens` = whole prompt (uncached + cache read + cache write); the split
  is priced separately into `est_micro_usd`. No schema change. Log line `provider_call`:
  outcome, mode, latency_ms, token counts only.
- Deps: `anthropic==2.13.0` (brings `httpx2`), `pillow>=11,<14`.

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
.venv/Scripts/python tools/sp11_latency.py   # SP-11 estimate only; live run needs --i-approve-spend
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
- SPR-05 follow-ups for SPR-14 (COMP-RESOLVER-GVP): replace `app/proxy/shape.py`
  (fuzzy grounding, AI-CONF, propose, `deadline_origin` from rules.json); count a model
  `sensitive` verdict as a guard miss in metric_daily (not counted yet).
- Failed provider calls (429/5xx) are not counted in usage_daily.provider_calls (they bill
  nothing); the client's 3-call cap is enforced on device.
- Single instance only in the beta (memory result cache). Redis trigger per DESIGN 4.4.
- A root `.dockerignore` (copy of `Dockerfile.dockerignore`) would also cover non-BuildKit
  builders; outside the server lane, left to the lead.
- Starlette warns that `httpx` with its TestClient is deprecated in favour of `httpx2`;
  harmless for now.
