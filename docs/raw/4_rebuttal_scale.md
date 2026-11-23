# 4 — Scalability rebuttal to red team (design only)

I accept the red team's frame: about 50 testers, one developer, 6 weeks. My test for every item: **is it a contract or on-disk format that existing users would have to migrate later?** If yes, do it now; if it is only capacity, defer it.

## A. Verdicts on my "beta foundation" items (scalability §8)

| # | Item | Verdict | Why (one line) |
|---|---|---|---|
| 1 | `core.db` / `index.db` split | **DEFEND** | Two files on day one is about 1 h. Splitting later means migrating every tester's data. It also makes R13's "exclude from backup" safe: back up `core.db` (confirmed actions, corrections), exclude the rebuildable `index.db`, so a restored phone keeps its history. |
| 2 | int8 vectors | **CONCEDE** | R7 cuts search to FTS5 only, so there are no vectors to format. If vectors are added later, they go in `index.db`, which is rebuildable, so the retrofit cost disappears. |
| 3 | Batched writes (~100 rows/txn) | **DEFEND (as a coding rule)** | The catch-up-on-open path still writes many rows. Batching is one wrapper function now, whereas removing jank later means hunting through every call site. |
| 4 | Newest-first ordering | **REVISE** | No backlog import (R13), but first catch-up is bounded by the install-time watermark. Keep `ORDER BY taken_at DESC` on the catch-up query: a one-word change. |
| 5 | `priority` field in `/v1/extract` | **REVISE** | Keep it as an optional enum (`live` default) in the request schema; the one-endpoint server ignores it. A schema field now avoids a breaking API version for testers' installed builds later. |
| 6 | Retry-After + full jitter + retry budget 3 | **DEFEND** | The red team keeps the budget of 3. Honouring `Retry-After` with jitter is about 20 lines of client code, and old builds that ignore it cannot be fixed from the server. |
| 7 | `cache_control` on the frozen prefix | **DEFEND** | One parameter. It cuts cost and may cut effective ITPM ~5x on an early-tier account (verify). |
| 8 | Separate live / backlog quotas | **CONCEDE** | No backlog in beta. The red team's daily counter plus the $25 provider cap is enough. |
| 9 | Stable idempotency key | **REVISE** | Put `HMAC(install_salt, sha256) + prompt_version + schema_version` in the request **now**. The key goes into installed clients, so it is a contract. Defer the server-side dedupe *store*: at 50 testers, double billing costs cents, so the endpoint stays stateless. |
| 10 | F8 counts without `user_id` | **DEFEND** | Leaving the field out of the payload costs nothing. Adding privacy after a per-user history exists means deleting data and rewriting the disclosure. |

## B. Final "scale-without-rewrite" foundation (each item a few hours or less)

1. `core.db` (backed up) + `index.db` (excluded, rebuildable: OCR blocks, FTS5, jobs). This closes C13.
2. A `rebuildIndex()` function that regenerates `index.db` from `core.db` and the photo library, which makes future index changes free.
3. One `writeBatch()` helper; serial image decode (at most 2 bitmaps at a time).
4. The install-time watermark (R9) plus newest-first catch-up.
5. API request schema: `idempotency_key` (HMAC, stable across retries; closes C24), `prompt_version`, `schema_version`, optional `priority`.
6. Client retry policy: at most 3 attempts per item, honours `429 Retry-After`, full jitter, then the "basic" card.
7. `cache_control` on the frozen prompt prefix.
8. F8 telemetry is aggregated `day × name × dim` with no `user_id`, and no content.
9. Keyset paging for the feed, plus a 10k seeded-data scroll test (R13).

## C. Deferred, with build triggers

| Deferred item | Build it when |
|---|---|
| Vectors (int8, then binary quantization + rescoring) | FTS5 misses more than ~20% of the beta's "find it" searches, or semantic search becomes a launch feature |
| Backlog import + backlog token budget + Batch API | Backlog import (FEATURES queue #4) is scheduled |
| Foreground service / native per-item loop / device-class throttling | Backlog import ships, or catch-up on a low-end tester phone takes more than 60 s |
| Server dedupe store (Postgres `idempotency` table) | Duplicate-key rate above 1% of requests, or more than ~500 users |
| Per-user + global token buckets, priority queues | Provider 429s above 1% for any 5-minute window, or more than ~1k DAU |
| Redis, JOBQUEUE flag, second provider endpoint | Sustained load above ~30 rps, or the first provider outage that lasts over 30 min |
| OTel backend, sampled traces, burn-rate alerts | Public launch, or spend above $100/month |
| `usage_daily` partitioning, log store outside Postgres | 100k users |
| Multi-region, EU residency | 100k+ users, or the first EU-market launch |
| Ask the provider for a higher rate-limit tier | 4 weeks before any public launch |

**Net:** of my original items, 4 survive unchanged (1, 3, 6, 7), 3 are revised to contract-only versions (4, 5, 9), 1 is unchanged privacy hygiene (10), and 2 are conceded (2, 8). The whole foundation is about 1–1.5 developer-days.
