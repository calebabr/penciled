# 3 — Scalability review (Round 3, design only)

Reviewer: Scalability. Inputs: FEATURES.md, chair_decisions.md, 2_architecture.md, 2_ai_pipeline.md, 2_platform.md / 2_privacy.md (skimmed). Nothing was run; every number is an **estimate (est.)** unless it is a price quoted by 2_ai_pipeline.md.

## 0. Load assumptions

| Assumption | Value (est.) |
|---|---|
| Daily-active share of registered users | 50% |
| Screenshots per active user per day | 20 (range 10–30). Note: architecture §10 assumed 3/day, which is 7x lower |
| Pass AI-GATE → LLM call | 50% → **10 calls / DAU / day** |
| Vision escalation | ~5% of calls (lower than AI §13's 12%, since D2 makes image upload opt-in, default off) |
| Peak-to-average | 5x (evening, plus semester-start waves of new users with backlogs) |
| Tokens per text call | 1,900 in (1,500 frozen prefix) / 450 out |
| New-user backlog | median 3k, heavy 10k–30k screenshots |

## 1. Server load at each scale

| | 10k users | 100k users | 1M users |
|---|---|---|---|
| DAU | 5k | 50k | 500k |
| Live LLM calls/day | 50k | 500k | 5M |
| Avg / peak calls/s | 0.6 / 3 | 6 / 30 | 58 / 290 |
| Peak input tokens/min, no cache | 0.34M | 3.4M | 33M |
| Peak input tokens/min, prefix cached | 0.07M uncached | 0.7M | 7M |
| Peak output tokens/min | 0.08M | 0.8M | 7.8M |
| Concurrent in-flight requests (5 s each) | 15 | 150 | 1,450 |
| Backlog calls/day (1% new users/day, 3k each, gate 50%, ~80% past-filtered) | 30k | 300k | 3M (Batch API) |

The FastAPI tier is not the problem. Async workers can hold about 1,450 open requests on 10–20 small containers. The problems are **provider token limits**, **retry amplification** and **what the server writes per request**.

## 2. On-device: heavy users and low-end phones

**Storage per 10k screenshots (est.).** Core rows + OCR text ~15 MB, `blocks_json` ~20 MB, FTS5 ~8 MB, vectors 15.4 MB (float32, as in the architecture schema) or 3.8 MB (int8, as in the AI pipeline). Total is **~45–60 MB**. At 30k it is ~150 MB. Two problems:
- The architecture says embeddings/FTS are "excluded from backup", but they are in the **same SQLite file**. Android Auto Backup caps the data at 25 MB, so the DB **passes that cap at ~4–5k screenshots** and backup silently stops.
- The two Round 2 docs disagree: the architecture uses `float[384]`, the AI pipeline uses int8. Changing this after launch means re-embedding every library.

**Search latency.** Brute-force KNN over 10k × 384 is ~4M multiply-adds, under 20 ms on any phone. The cost is I/O: on a 2020 budget Android with eMMC (~150 MB/s), a cold scan of 15 MB float32 takes ~100 ms. At 50k items it is 77 MB, so ~500 ms cold, which breaks the 300 ms p95 budget. With int8 it is 19 MB (~130 ms). With binary quantization plus int8 rescoring of the top 200 it is ~2.4 MB (<30 ms). FTS5 BM25 stays under 30 ms to 50k. The feed (keyset paging + FlashList + OS thumbnails) is unaffected by library size.

**Backlog import time.** AI §11 estimates 3–10 images/s. That holds for a mid-range phone in the foreground only. On a low-end phone (est. per item):

| Step | Time |
|---|---|
| Decode 1080×2400 | 150–300 ms |
| ML Kit OCR | 400–1,200 ms |
| MiniLM ONNX on CPU | 60–150 ms |
| JS-bridge and SQLite write | 20–50 ms |
| **Total** | **~0.7–1.7 s/item** |

That gives **10k in 2–5 h** and **30k in 6–14 h** of foreground-equivalent work. Two platform limits make it worse:
- **Android:** a WorkManager worker is stopped after ~10 min, so long runs need a foreground service. Android 15 also caps the `dataSync` foreground-service type at about 6 h/day (verify).
- **iOS:** `BGProcessingTask` runs only when the OS chooses (charging, idle). In practice an iOS backlog finishes over **several nights or while the app is open**.

If OCR, embedding and writes all run on the RN JS thread, the UI will also stutter during the import. Memory on a 3 GB phone (RN ~150 MB + ML Kit + ONNX ~60 MB + decoded bitmaps) is fine if processing is serial, but OOM-kills are likely if more than 2 images are decoded at once.

**sqlite-vec loading.** Runtime extension loading is restricted on iOS. Use expo-sqlite's bundled sqlite-vec build option (verify for the SDK version). Also check that `vec0` accepts a TEXT primary key; otherwise key it by `screenshot.rowid`.

## 3. Throughput, rate limits, retries, idempotency

- **Provider rate limits.** Anthropic limits are per organisation, per model and by spend tier (verify the current ITPM/OTPM numbers in the console). A new account's early tiers are likely to be below the 0.3M ITPM peak at 10k users. A **single tester's 10k import**, if the "upcoming" items go real-time, could hit the limit on its own during beta. Cache reads may not count toward ITPM for current models (verify). If so, caching the 1,500-token frozen prefix cuts effective ITPM ~5x. That makes `cache_control` on the prefix a throughput fix, not only a ~15% cost fix.
- **Retry amplification.** The proxy does 1 retry and the client up to 8 backoff attempts, so one item can cost up to 18 provider calls during a degradation. After an outage, every device's job queue wakes on reconnect at once (thundering herd).
- **Idempotency bug.** The key `sha256 + attempt` changes on every retry. That defeats deduplication, and a timed-out request that the provider actually finished is billed twice. The 10-min cache must also be shared across instances (it is not in a scale-to-zero container's memory). Finally, the raw SHA-256 of a user's image is a content fingerprint stored on the server; use HMAC(install salt, sha256).
- **Quota conflict.** The 200/day beta cap conflicts with AI §11's "no hard daily cap" for backlog. Split it into a **live cap** and a **backlog token budget**.

## 4. Postgres and server storage growth

Postgres is the right choice for users, devices, quota and deletion receipts; at 1M users these are under 5 GB. Two tables in the design are the wrong shape for it:

| Table | 1M-user volume (est.) | Problem |
|---|---|---|
| `request_log` (one row per request) | 5M rows/day × ~150 B ≈ 0.75 GB/day, ~23 GB at 30-day TTL, 60+ inserts/s average | OLTP write load used as a log store; TTL purge churns vacuum |
| `metric_counts(user_id, day, name, dim)` | ~20–40 rows/DAU/day → 10–20M rows/day | Biggest table by far; per-user analytics is also a privacy liability |
| `usage_daily` | 500k upserts/day, ~18 GB/yr | Fine with monthly partitions and roll-up after 90 days |

Indexing as designed is adequate. Add `usage_daily(day)` for spend roll-ups, and partition `usage_daily` monthly at 100k+.

## 5. Multi-region

Not needed for latency: the LLM call (1.5–3.5 s) dwarfs an extra 150 ms of round trip. It is needed for:
- **Availability at 1M:** active-passive in a second region. Postgres is only consulted for auth and quota, so a regional Redis cache of tokens and quota keeps the service up during a Postgres failover.
- **Provider redundancy:** route the same model through a second endpoint (for example a cloud marketplace offering of the same Claude model, verify) behind the existing adapter.
- **EU users:** processing location of the provider; there is no content at rest, so the data-residency scope is small.

Defer all of this to the 100k+ stage.

## 6. Observability without content

Use OpenTelemetry traces and metrics with an **allow-listed attribute schema** (enums, counts, durations, model, prompt_version, status). Do not use free-text log lines on the extract path. SEC-LOG-NOCONTENT and the CI grep test cover enforcement.
- **Server metrics:** request rate and latency histograms per model/prompt_version; provider 429/5xx/refusal rates; queue depth and oldest-job age; cache-hit ratio; escalation rate; AI-GROUND failure rate (catches prompt regressions); $/hour.
- **Client metrics (aggregated, F8):** time-to-card histogram buckets, gate drop rate, backlog items/hour by device class.
- **Alerts:** spend burn rate above 2x the 7-day baseline (auto-trips the kill switch at 4x); provider 429 above 2% for 5 min; GROUND failures +50% after a prompt_version change; oldest live job above 60 s.

## 7. Cost per active user per month (est.)

| | 10k users | 100k users | 1M users |
|---|---|---|---|
| LLM live (10 calls/day, ~$0.035/100 calls with caching and 5% escalation) | $0.11 | $0.11 | $0.10 (volume discount possible) |
| Backlog (one-off, ~$0.50–2 per 10k import, Batch API), amortised | $0.02–0.05 | same | same |
| Infra (containers, Postgres, Redis, OTel backend) | ~$50/mo → $0.01 | ~$600/mo → $0.012 | ~$5k/mo → $0.01 |
| **Total per DAU** | **~$0.15** | **~$0.15** | **~$0.13** |

These assume 20 screenshots/day. At 30/day with the Sonnet escalation share from AI §13, the worst case is ~$0.40 per DAU. **Escalation rate is the cost lever; observability vendor pricing is the infra risk** (per-span pricing at 5M requests/day can exceed compute, so sample traces at 1–5%).

## 8. The first three bottlenecks, in order of appearance

**B1. On-device backlog import on low-end phones (appears with the first beta tester who has 10k screenshots).** This shows up as hours of work, background kills, UI jank, and the DB passing the backup cap.
- Fixes:
  - Split into `core.db` (backed up: screenshot, proposed/executed actions, corrections, kv) and `index.db` (excluded and rebuildable: OCR blocks, FTS5, vectors, jobs).
  - Store vectors as **int8** from day one.
  - Write in batched transactions of ~100 rows.
  - Order the backlog newest first, with embeddings deferred after OCR, gate and resolve.
  - Process images serially; bitmap decode at most 1–2 at a time.
  - Show a resumable progress UI. On Android use a foreground service; on iOS, say plainly that it "continues while the app is open or charging overnight".
- **Beta foundation:** DB split, int8 schema, batching, newest-first ordering. **Can wait:** binary quantization, moving the per-item loop into a native module, device-class throttling.

**B2. LLM provider rate limits and bursts (≈1–5k DAU, or earlier from one large import).**
- Fixes:
  - Server admission control: a per-user token bucket plus a global bucket sized to the provider tier.
  - Three priority classes: live, then upcoming backlog, then Batch API.
  - `429 + Retry-After` that the client honours, with full jitter.
  - A retry budget: the client stops after 3 server-side failures per item and shows the AI §9 "basic" card.
  - `cache_control` on the frozen prefix.
  - Ask the provider for a tier increase before any public launch.
- **Beta foundation:** a `priority` field in `/v1/extract`; Retry-After and jitter handling in the client; prompt caching; separate live and backlog quotas. **Can wait:** Redis buckets (Postgres counters are fine below ~30 rps), turning on the JOBQUEUE flag, a second provider endpoint.

**B3. Server state in the wrong places (≈50–100k users).** This covers the per-request `request_log` and per-user `metric_counts` growing in Postgres, plus an idempotency cache that does not survive multiple instances.
- Fixes:
  - The idempotency key = HMAC(install salt, sha256) + prompt_version + schema_version, stable across retries, so a user "retry" bumps an explicit `rerun` counter instead. Store it in Postgres (`idempotency(key pk, status, result_ref, expires_at)`) in beta, Redis later.
  - Send request metadata to OTel/log storage with a TTL, not Postgres.
  - Have F8 uploads aggregate into a **day × name × dim** table without user_id; keep any per-user rows only for the beta cohort.
- **Beta foundation:** the stable idempotency key (it is a contract change and a double-billing bug). Also send F8 counts without user_id so that no per-user analytics history accumulates. **Can wait:** OTel backend migration, partitioning, Redis.

## 9. Smaller items for DESIGN.md
- Reconcile where AI-GROUND/RESOLVE run (architecture: device; AI pipeline: server). Either scales; device-side matches D4 and the offline story.
- Restate the architecture §10 load at 20 screenshots/day (58 calls/s average at 1M, not 35 req/s at 3/day).
- Add the search p95 to the budget table explicitly for a **2020 low-end Android at 30k items** (≤500 ms), as well as for the 2022 mid-range phone at 10k (≤300 ms).
