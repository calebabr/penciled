# Purchases follow-up: Feature Prioritizer

Inputs: FEATURES.md, BUILD_HANDOFF.md §2 and §8, SPRINT_PLAN.md (capacity), chair_decisions.md (D23), 1b_prioritizer.md, 1a_behavior.md. `raw/purchases/1_analyst.md` did not exist when I wrote this. Claims marked **[unverified]** come from my own knowledge.

## Verdict: I reject the default
Do not add a Purchase action type to beta, not even return-window only. Fold the return-window reminder into post-beta queue #1 (receipt → expense) as its first slice. Beta gets one zero-build passthrough and some day-one logging (below).

Why the default fails here:
1. **No capacity.** At 7 sessions a week the plan has about zero slack, and at 6 a week it is 3–4 sessions short even after all 12 cuts. The user declined to move the date (D23). Purchase extraction plus return reminders means a new class, schema, validator, card variant, F2f grounding rules, eval labels and executor presets. My estimate is **4–6 sessions [unverified estimate]**, which is more than the whole planner cut list saves (~5.85).
2. **It conflicts with the sensitive guard.** Receipts and order confirmations usually show card last-4, addresses and long order numbers. The guard is biased to false positives (SP-12), and the payload scan blocks any run of 7+ digits. So many receipts would go local-only and get no card. Making them work means loosening a release-blocking safety gate in the last 8 weeks. That is the wrong trade.
3. **The return window is usually not on the screenshot.** Order confirmations often leave out "return by" **[unverified]**. Working it out from merchant policy breaks the "never invent a field" rule, and F2f's hard gate means an ungrounded date can never be Ready.
4. **The holiday timing is weaker than it looks.** Hard rule 8 means no pre-install screenshots and imports are capped at 20. Most holiday purchases happen before install, and many holiday return windows end in mid-to-late January **[unverified]**.
5. **It does not strengthen the magic moment.** It competes for SP-5 hand-labelling, which is the human long pole, and for tester attention.

## Scores (1–5; C: 5 = cheap)
| Part | V (evidence) | D | R (extract/determine) | C | Decision |
|---|---|---|---|---|---|
| Purchase extraction (merchant, date, total, items) | 3: receipts are #2 by S1 22/55 (n=55, ±1) | 2: retailer apps and email order trackers exist **[unverified]** | 3: total and date are groundable; line items are messy | 2 | **POST-BETA**, merged into queue #1 |
| (a) Return-window deadline + reminder | 4: money at stake, time-bound decay (1a). The return use itself is unmeasured | 3 | 4 if printed, 1 if inferred from policy | 2 | **POST-BETA queue #1, slice 1.** Beta: printed-date passthrough only |
| (b) Warranty end + reminder | 2: fires months or years later, so the beta cannot measure it | 3 | 1: term rarely printed; needs product-to-term lookup | 2 | **POST-BETA, unranked** (below #7) |
| (c) Recall check (e.g., CPSC) | 2 | 4 | 1: fuzzy product-name matching gives false alarms; needs model numbers | 1: external data feed, server job, push | **REJECT.** It is also a proactive notification, a category already rejected for beta |
| (d) "Things I own" view + insurance export | 2 | 2 | 2 | 2 | **REJECT for now.** Inventory is a different product and overlaps the rejected auto-collections. Revisit after expense CSV exists |

## Beta passthrough (no new component, ~0 sessions)
If a receipt screenshot passes the guard and shows a **printed** "Return by / Returnable until ‹date›", the existing **deadline** class may propose it like any other deadline. It uses the same card, grounding and alarms as everything else. Constraints:
- No prompt change, no new class and no merchant-policy inference.
- No eval-set additions beyond what SP-5 would label anyway.
- Displaces nothing. If it needs any work, drop it.

**Trust risk of a wrong deadline:** asymmetric and monetary. A reminder that is too late means a lost refund, and users blame the app. That is worse than a mis-timed flyer. So:
- Only grounded printed dates.
- Never inferred windows.
- Inferred year and past-date rules stay blocking per D20.

## If the Chair overrides and wants a thin return-window slice in beta
Explicit displacement at 7 sessions a week. All of it lands on items the plan already treats as last resort:
- **Cut 12 Search/F6** (saves 1–1.5) **plus cut 11 iOS catch-up** (saves 1). Both are Chair decisions and both amend FEATURES (F6(b), F1(b)) and EVAL-BAR-12/13.
- **Even that covers only ~2.5 of ~4–6 sessions.** It also needs a guard carve-out (card last-4 and order numbers redacted rather than blocking), which reopens SP-12 and EVAL-SAFE-01.
- At 6 sessions a week it is not achievable without the Android-only beta.

I recommend against all of this.

## Log from day one (enums and counts only; hard rule 3 holds)
These are cheap only if they go into `shared/` contracts **before CP0 freezes v1 on Nov 25**:
1. **`nothing_subtype` enum** on "nothing to do": `receipt_order | shipping | booking | meme | other`. This turns the #2-category guess into measured category mix (F8).
2. **Guard reason enum** with counts per subtype. It tells us how many receipts the guard blocks, which is the cost of the future carve-out.
3. **`deadline_origin` flag** on deadline cards: `printed_return_by | other`. It records how often return windows are actually printed, which is the key reliability unknown.
4. Confirm, edit and dismiss rates for deadline cards with that flag. This is the baseline for queue #1.
5. An optional one-tap post-beta survey item: "Did you screenshot a purchase you meant to return?" (count only).

**Trigger to promote queue #1:** receipt/order is ≥15% of processed screenshots, and `printed_return_by` shows up on ≥30% of them. Below that, ship expense CSV without return reminders.
