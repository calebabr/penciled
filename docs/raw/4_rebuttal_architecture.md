# 4 — Architecture rebuttal to red team (design only)

## R1/R2: iOS from Windows. CONCEDE + REVISE
- **Build path:** EAS Build (cloud macOS) → EAS Submit → TestFlight. JS work runs on a physical iPhone through the Expo dev client, served by Metro from Windows, so a cloud rebuild is needed only when native dependencies change. Budget: Apple Developer ($99), plus one paid EAS month for Dec–Jan if the free iOS build quota runs out (check the current quota).
- **Surviving iOS scope:** the main app, a share extension from a config plugin (`expo-share-intent`), RN ML Kit OCR, and a catch-up scan on open via `expo-media-library`, run since the install watermark. If that module doesn't expose the screenshot subtype, filter by device-screen dimensions. **Zero custom Swift.** Dropped: Vision, the PhotoKit observer, App Intent, Back Tap and the notification content extension.
- iOS magic moment = share → card in ≤ 2 s. The card starts in the "Reading…" state and is ready by the shared SLO (C16).

## R3: app-closed Android trigger. REVISE: thin Kotlin, server resolves
We don't run a headless-JS spike, which takes that risk out of week 1.
- **Kotlin `ScreenshotWorker`** (WorkManager content-URI trigger plus a network constraint): ML Kit OCR → guard/redact using `guard_rules.json` → `POST /v1/extract` → writes the response to `inbox/<key>.json` → posts the notification text the server returned. It never opens the app's SQLite, so there's no cross-runtime locking.
- On open, JS ingests `inbox/` into the DB. The iOS share path and the in-app path call the same endpoint from TS.
- **Split:**
  - Device: capture, OCR, guard/redact, DB, search, confirm, execute, undo.
  - Server: extract, plus the single **AI-RESOLVE/validate (Python)**: src-quote check, date resolution, flags with `blocking`, the ladder and the notification copy.
  - The device runs only a zod schema check. The confirm sheet uses native date pickers, so the device needs no date parser.
- The guard has two implementations of one JSON ruleset. Both must pass a shared fixture file in CI.

## C1–C24
| # | Answer |
|---|---|
| C1 | One Kotlin module plus the config-plugin share extension. No other targets. |
| C2 | Android first for auto-detect. iOS TestFlight runs in parallel. Hello-world builds on both in week 1. |
| C3 | RN ML Kit on iOS, ML Kit Android in the worker. No Vision. |
| C4 | WorkManager. |
| C5 | Server (Python), only there. |
| C6 | AI §4's model schema is internal to the server. The device receives `ProposedAction{fields{value,flag,blocking,src_span}}`. |
| C7 | The server sets `blocking`: an inferred year is shown but doesn't block, and AM/PM ambiguity blocks. The UI obeys the field. |
| C8 | The device sends `image_allowed` per request. One size: 1280 px long edge, JPEG q70. The default policy goes to the Chair after the week-1 spike (R4d). |
| C9 | Chair D1 stands. |
| C10 | "Send anyway" is dropped. |
| C11 | Full access on iOS (D7). Onboarding copy says so. |
| C12 | CONCEDE. The copy states the provider's verified retention plus our 10-min result cache. |
| C13 | DB split (below). |
| C14 | Moot: no embeddings. |
| C15 | Opaque invite token, no expiry, revocable. 100 extractions/day per token. |
| C16 | One SLO, screenshot → notification/card: p50 ≤ 5 s, p95 ≤ 10 s. |
| C17 | 10 s toast. History keeps undo. |
| C18 | Actions owner decides. The server ladder is code, so it's one constant. |
| C19 | Search is on-device FTS5 only, offline. |
| C20 | Item delete is local. `DELETE /v1/me` removes the token row, counters and cache rows. |
| C21 | Android asks for notifications right after Photos. |
| C22 | Calendar alarms fire from the OS. The bar is p95 < 2 min. |
| C23 | No backlog in the beta. Install watermark. 20/day budget. |
| C24 | Fixed (below). |

## C24, R9: retry and idempotency. CONCEDE + REVISE
- `Idempotency-Key = HMAC(install_salt, sha256) : prompt_version : schema_version : rerun`. It stays the same across automatic retries. A user "Retry" increments `rerun`.
- Server: Postgres `idempotency(key pk, status, result_json, expires_at = +10 min)`, purged on read after it expires. A duplicate key while the first request is in flight returns `202 retry_after`.
- Retry budget: **the proxy makes 0 retries.** The client makes at most 3 attempts (30 s, 5 min, 30 min, ±30% jitter), then shows a "basic" card. That caps it at **3 provider calls per item**.

## R7/R13/C13: DB split. REVISE; embeddings CONCEDE
- `core.db` is backed up and holds `screenshot` (metadata), `proposed_action`, `executed_action`, `correction`, `job`, `kv`. At about 1 KB per item, 10k items is about 10 MB, under the 25 MB cap.
- `index.db` is excluded from backup (Android `dataExtractionRules`; iOS Caches). It holds `ocr` text and `ocr_fts`. Both can be rebuilt by re-running OCR from `asset_ref`, newest first.
- **Embeddings, sqlite-vec and onnxruntime are out of the beta.** If v2 brings them back, they get their own table in `index.db`, keyed by rowid, with no change to core.
- No SQLCipher. We rely on the OS sandbox and say so in the privacy copy.

## R8: server minimalism vs scaling without a rewrite. CONCEDE scope, DEFEND five seams
**Beta:** one FastAPI container with `POST /v1/extract` and `DELETE /v1/me`, plus 3 Postgres tables (`token`, `usage_daily`, `idempotency`) and a $25/month provider cap.
- Dropped: JWT refresh, attestation, remote config, OTel, `request_log`, `devices`, `jobs`, Sonnet.
- `min_app_version` and F8 counters ride in the extract request/response. Counters are stored without a token id.

**The seams that make 1M a configuration change, not a rewrite. They cost almost nothing now:**
1. `/v1` plus `schema_version`.
2. A stable idempotency key, stored in Postgres, not in memory (a scale-to-zero container loses its memory).
3. The client already treats `202 retry_after` as a retry. That makes the later queue a server-only flag.
4. A bearer header. Swapping the opaque token for a JWT changes how tokens are issued, not the code that calls the API.
5. A provider adapter, so model or batch pricing is a server change.

Not built: Redis, queue workers, partitioning.
