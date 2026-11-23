# shared/ contracts changelog

## Rule

Additive only after CP0 (2026-11-25); any change needs a version bump and a note; shared/ is read-only except in a dedicated bump session.

- "Additive" means new optional properties, new top-level schemas, or new enum values that
  older readers can drop or ignore. Removing or renaming a property, making an optional property
  required, narrowing a type or removing an enum value is a breaking change: it needs
  `schema_version` 2 (and `/v2` side by side for one release, DESIGN 3.7).
- Every change: edit `shared/schema/*.schema.json`, run `npm run generate -w @penciled/shared`,
  add fixtures, bump the package versions (`shared/package.json`, `shared/python/pyproject.toml`),
  and add an entry below. CI fails if generated code drifts from the schemas.
- `rules.json` content (SPR-08) and `thresholds_vN.json` (COMP-CALIB, human-approved
  baseline-bump commit) are data, not contract changes; their formats are frozen here.

## 1.0.0 (contracts-v1, schema_version 1), 2026-11-23

First frozen contract set (SPR-02, COMP-CONTRACTS), including the purchases extension (D24)
and the pricing foundation (D25).

- `extract_request` (POST /v1/extract body). No `tier` property: a client-sent tier is dropped.
- `extract_response` (200 body): <= 3 `ProposedAction`s, `nothing_subtype` on nothing-to-do
  results, optional `quota{tier, state: ok|near|exhausted}`.
- `proposed_action`: `event` | `deadline`; deadlines carry `deadline_origin`
  (`printed_return_by` | `other`).
- `error`: one envelope for every non-200 body (incl. 202 `in_flight` + `retry_after`,
  429, 413, 422 content-free `issues`, 426 `min_app_version`, 503 `basic`).
- `worker_config` (app -> Android worker, `format_version` 1).
- `inbox` (Android worker -> app): `pending_app` | `local_only` | `none` | `extracted`.
- `guard_result`: `guard_reason`, per-reason counts, `receipt_like`, chat verdict, actionable.
- `behavior_event`: core.db row plus purchases and pricing enums (`pro_door_event`,
  `pro_feature`, `wtp_bucket`, `plan_pref`, `usage_day_bucket`, `cap_tier`, `shadow_cap_hit`,
  `import_cap_hit`, `search_zero_result`).
- `token_claims`: server-controlled `tier` (`free` | `pro`, default `free`).
- `rules` (`shared/rules/rules.json` format) and `rules_fixture` (`shared/rules/fixtures/`).
- `thresholds` (`shared/thresholds/thresholds_vN.json` format).
- Generated zod 4.6.7 types (`shared/ts`, package `@penciled/shared`) and pydantic v2 models
  (`shared/python/penciled_contracts`). Unknown keys are dropped on parse in both.
