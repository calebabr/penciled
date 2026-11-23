# shared/STATUS.md (COMP-CONTRACTS)

**State:** contracts v1 done in SPR-02 (2026-11-23), waiting for the `contracts-v1` tag. Freeze at
CP0, 2026-11-25. After that, `shared/` is read-only except in a dedicated bump session
(see CHANGELOG.md).

## Acceptance checklist
- [x] JSON Schemas (2020-12), the source of truth, in `schema/`: extract_request, extract_response,
      proposed_action, error, worker_config, inbox, guard_result, behavior_event, token_claims,
      rules, rules_fixture, thresholds (+ common $defs).
- [x] Purchases extension (D24): `nothing_subtype`, `guard_reason` counts + `receipt_like`,
      `deadline_origin`, matching behavior_event values.
- [x] Pricing foundation (D25): `tier` on token claims (default free, never read from the client),
      optional `quota{tier,state}`, pricing metric enums.
- [x] Generated zod (`ts/generated.ts`) and pydantic v2 (`python/penciled_contracts/generated.py`)
      from `tools/generate.mjs` (no third-party generator). CI drift check:
      `npm run check:generated -w @penciled/shared` (also run inside `npm test` and pytest).
- [x] Unknown keys dropped on parse in both languages (zod strip, pydantic `extra="ignore"`).
- [x] Round trip on 41 fixtures (>= 20) incl. worker_config, inbox pending_app, one nothing-to-do per
      subtype, one deadline per origin, responses with and without quota, a request whose client
      `tier` is dropped. `schema_version` present in both directions.
- [x] 19 negative fixtures rejected by zod, pydantic and the JSON Schema (missing/wrong
      schema_version, > 3 actions, bad enums, null for an optional, free-text dims).
- [x] `rules/rules.json` (valid placeholder, `r0-placeholder`) + `rules/fixtures/format_example.json`.
- [x] `thresholds/README.md` (no thresholds file; COMP-CALIB writes v1).
- [x] CHANGELOG.md with the additive-only rule.
- [ ] Tag `contracts-v1` (lead).

## Commands
```
npm run generate -w @penciled/shared        # regenerate after a schema edit (bump session only)
npm test -w @penciled/shared                # drift check + zod -> pydantic -> zod round trip
server/.venv/Scripts/python -m pip install -e shared/python[dev]
server/.venv/Scripts/python -m pytest -q shared   # pydantic -> zod -> pydantic + JSON Schema checks
```
Node >= 22.18 runs the `.ts` tests and helpers directly (type stripping). The node test looks for
python in `$PENCILED_PYTHON`, then `server/.venv`, then `python3`/`python`.

## Parse rules (both languages)
- Strict types (no "1" -> 1, no 1 -> true). Optional non-nullable properties may be omitted, not null.
- Canonical output: absent optionals left out, explicit nulls kept, schema defaults filled
  (`priority` = live, `tier` = free). Python: `to_json_dict()` / `penciled_contracts.canonical()`.
- Known gap: JSON `1.0` for an integer is accepted by zod (JS has one number type) but rejected by pydantic strict.

## Notes for consumers
- `rules/rules.json` content is a placeholder; SPR-08 (COMP-RULES) owns the real patterns and
  parity fixtures. Regexes must stay in the ECMAScript / java.util.regex common subset.
- Cross-field rules are NOT in the schemas and belong to the server: `nothing_subtype` iff
  class nothing; 422 when `image_b64` is set with `is_chat` or not `image_allowed`.
- Counter `name`/`dim` are token-shaped strings; the server validates them against the enums in
  `behavior_event.schema.json` $defs (COMP-METRICS adds the general F8 names).
- The server's current 422 body (`{"error":"invalid_request"}`, SPR-01) predates `error.schema.json`;
  SPR-04 should emit `{schema_version, code, issues?}`.
