# SPRINT_IMPACT.md: purchases extension (D24)

Status: design only; nothing built, installed or run. (added: purchases extension; D24). Sources: raw/chair_decisions.md D24, FEATURES.md F2(f) and F8 extension, BUILD_HANDOFF.md (COMP-CONTRACTS, COMP-EVALSET, COMP-METRICS, cut list items P1 and P2). SPRINT_PLAN.md is **not edited** by this file; the planner applies the changes in the last section.

## 1. Sprints that change

| Sprint | Change | Deadline | Effort *(est.)* |
|---|---|---|---|
| **SPR-02** Contracts v1 | Add enum/boolean fields: `nothing_subtype` (`receipt_order \| shipping \| booking \| meme \| other`), `guard_reason` counts + `receipt_like`, `deadline_origin` (`printed_return_by \| other`), matching `behavior_event` enum values. Add one nothing-to-do fixture per subtype and one deadline per origin to the 20 round-trip fixtures. | **Before the Nov 25 CP0 freeze** (SPR-02 is a W1 sprint; after the freeze it needs a version-bump session) | ~0.1 session, absorbed in the 1-session SPR-02 if possible |
| **SPR-06 / SPR-21** Eval set (own images in SPR-06, generator + labels in SPR-21) | 10 to 15 receipt/order fixtures inside the ~150 images, not additional: with/without printed "Return by", policy sentence without a date, order number + card last-4, one guard-blocked, ≥2 injection-in-receipt cases (counted toward the 10 injection fixtures). Labels carry `nothing_subtype` and `deadline_origin`. Synthetic or own only. | within SPR-21 | ~0.2 session |
| **SPR-25** Beta counts and behaviour log | Enum dims on `metric_daily` for the new fields; F8 report computes the promotion trigger (receipts ≥15% of processed screenshots AND ≥30% of those with a printed return date); scripted 10-card session includes one receipt; EVAL-BAR-14 scan covers the new dims. | within SPR-25 | ~0.2 session |
| SPR-08 (guard rules) | Add the `receipt_like` keyword list and the `deadline_origin` evidence pattern to `rules.json` (Kotlin and TS parity fixtures). Guard thresholds and patterns are **not** changed. | within SPR-08 | ~0.1 session (counted in the total below) |

**Total added effort: ≤ ~0.5 session** (sum of the rows above is ~0.6 at the top end; the planner books 0.5 and absorbs the rest in existing slack, since SPR-02 and SPR-25 are S-sized and Low risk). This is an estimate, not a measurement.

## 2. What moves

**Nothing.** No sprint is added, delayed, reordered or resized in the plan's session count beyond the ≤ ~0.5 absorbed above. No dependency edges change. The critical path (20 sessions) is unchanged because none of the additions are on it.

## 3. Does Jan 13 to 15 hold

**Yes.** The beta date, RC on Jan 14 and testers on Jan 15 (D23) are unchanged. At the baseline capacity there is no slack to spend, so the cost is protected by cut items **P1** and **P2** (BUILD_HANDOFF §8), which are taken before any item of the original list if the plan is behind at the first trigger (T1). P2 can only be cut before Nov 25 without a contracts version bump.

## 4. Explicitly NOT added

- No Purchase action type, no `kind:"purchase"`, no new class in the beta.
- No retailer policy table, no return-window computation, no policy inference in the prompt or in code.
- No new screen, component, state, token or notification (the passthrough uses the existing CMP-ACTIONCARD deadline variant).
- No recall matching (rejected; CPSC data sparse, fuzzy matching, false alarms).
- No "things I own" view and no insurance export (rejected).
- No change to the sensitive guard, SEC-REDACT or any threshold; receipts that trip the guard stay ST-SENSITIVE, counted only.
- No new permission, server table or content logging.
- The post-beta PUR-* components are unsized and unscheduled.

## 5. Exact changes the sprint planner must make to SPRINT_PLAN.md (do not apply here)

1. **SPR-02 Goal and Exit:** append `nothing_subtype`, `guard_reason` counts + `receipt_like`, and `deadline_origin` enums to the schema list; Exit: the 20 round-trip fixtures include one nothing-to-do per subtype and one deadline per origin. Add "**must land before the CP0 freeze Nov 25**" and keep the tag `contracts-v1`.
2. **SPR-08** (guard/rules): add `receipt_like` keywords and the `deadline_origin` pattern to `rules.json` and the parity fixtures; add "guard thresholds unchanged".
3. **SPR-06 and SPR-21** (COMP-EVALSET slices A and B): add the 10 to 15 receipt fixtures (inside the ~150), the labels, and the ≥2 injection-in-receipt cases; Exit unchanged except the manifest counts.
4. **SPR-25** (COMP-METRICS, COMP-BEHAVLOG): add the new enum dims, the promotion-trigger line in the F8 report, and the receipt in the scripted session; Exit: EVAL-BAR-14 still 0 content.
5. **Capacity table / session count:** add ≤ ~0.5 session absorbed across SPR-02, 08, 21 and 25 (no new sprint number, no change to W1 to W4 session counts shown as whole numbers unless the planner chooses to round up).
6. **Cut-trigger table (T1):** add **P1** (receipt fixtures) and **P2** (purchase logging fields) above item 0 in the cut list; P2 is decidable only until Nov 25. Update the item numbering references accordingly (original items 0 to 12 keep their numbers).
7. **Risks table:** add one row: "Receipt logging data shows receipts <15% or printed dates <30% (promotion trigger not met)", Low / Low, mitigation: ship expense CSV without return reminders, no Purchase type.
8. **CP0 checklist (Nov 25):** add "purchase logging enums are in `contracts-v1`".

---

# Pricing pass (added: pricing pass); D25

Status: design only; nothing built, installed or run. Sources: raw/chair_decisions.md D25, raw/pricing/1_pricing.md §5 to §7, DESIGN.md §3.6/§3.7, BUILD_HANDOFF.md (COMP-CONTRACTS, COMP-QUOTA, COMP-METRICS).

## P1. Contracts-freeze additions
Additive fields inside `contracts-v1`, **must land before the CP0 freeze on Nov 25**: `tier` token claim (default `free`), optional `quota{tier,state}` response object, and the pricing metric enums (`pro_door_event`/`pro_feature`, `wtp_bucket`, `plan_pref`, `shadow_cap_hit`, `import_cap_hit`, `usage_day_bucket`, `search_zero_result`, `cap_tier`). Per-tier limits are COMP-QUOTA config.
- Effort: **<= ~0.25 session in total** *(est.)*, split across SPR-02 (contract fields and fixtures) and the metrics sprint SPR-25 (enum dims). COMP-QUOTA config rides inside the existing server-core sprint.
- **Nothing displaced.** No sprint is added, resized or reordered; the whole-number session counts stay as they are.
- The optional Settings "Pro preview" page (cut-list item P0) is about ¼ session of UI work inside the Settings sprint; it is the first cut and not needed for the schedule.

## P2. Jan 13 to 15 holds
No change to the date (D23). Billing, IAP, paywall, tier values and prices are post-beta and unsized (PRICE-TIERS, PRICE-IAP). The free core loop and beta scope are unchanged.

## P3. Exact changes for the planner to make in SPRINT_PLAN.md (listed, not applied)
1. **SPR-02 Goal and Exit:** add `tier` (token claim), the optional `quota{tier,state}` response object and the pricing enums to the schema list; Exit: the 20 round-trip fixtures include one response with `quota` and one without, and an unknown client-sent `tier` is dropped. Keep "must land before the CP0 freeze Nov 25" and the tag `contracts-v1`.
2. **COMP-SERVER-CORE sprint:** add "per-tier limits read from config (`tier_limits`); `tier` from the token record only" to the Goal and a config-changes-the-limit test to the Exit.
3. **SPR-25** (COMP-METRICS, COMP-BEHAVLOG): add the pricing enum dims; Exit: EVAL-BAR-14 still 0 content.
4. **Capacity table:** add <= ~0.25 session absorbed across SPR-02 and SPR-25; no change to whole-number session counts.
5. **Cut-trigger table (T1):** add **P0** (Pro preview row) above P1 and P2 in the cut list (cut first); original item numbers unchanged. The contract and metric fields are decidable only until Nov 25.
6. **Settings sprint:** note the optional Pro preview row as the first cut (UI.md §4.4).
7. **CP0 checklist (Nov 25):** add "`tier`, `quota` and pricing metric enums are in `contracts-v1`".
8. **Post-beta list:** add PRICE-TIERS and PRICE-IAP, unsized, dotted.
