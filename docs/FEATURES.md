# FEATURES.md — Locked beta feature set

Status: LOCKED at end of Round 1 (2026-11-18). Later rounds design for this set only. Changes only via the Round 4 red-team adoption step, recorded at the bottom.
Raw inputs: `raw/1a_competitors.md`, `raw/1a_behavior.md`, `raw/1a_ideas.md`, `raw/1b_prioritizer.md`.

## Evidence quality warning
Category evidence is thin: the only counted survey is n=55 [S1], the Mottelson 31% "memory offload" figure is secondhand [S3], and no Reddit or Play Store review text was retrievable. Competitor "nobody ships X" claims are absence-of-evidence. Consequence: the beta must instrument itself (confirm rate, per-field edit rate, "nothing to do" rate, category mix) so the beta itself produces the missing evidence.

## Core principle (non-negotiable)
The model reads and proposes; deterministic code validates and executes; the user confirms. No action happens without a user tap. Every proposal shows its extracted fields, editable first.

## The core loop (5 steps)
1. **Capture** — user takes a screenshot (or shares/imports one).
2. **Understand** — the app reads it, classifies it (event / deadline / nothing to do), extracts typed fields, and flags uncertain ones.
3. **Propose** — an "action-ready" notification and card show a pre-filled calendar event or reminder.
4. **Confirm** — user fixes any flagged field in a sheet and taps once.
5. **Done + undo** — code writes to the calendar/reminders; a toast offers Undo; the action is logged.

## The magic moment
"I screenshotted a flyer / group-chat plan, and a few seconds later my phone told me it was ready: a filled-in event with the right date, and its RSVP deadline as a reminder. I tapped Review, checked the one highlighted field, and tapped Add." (Beta: Review then Add, 2 taps; no one-tap Add from the card or notification, D19/D20.)
Why this one: events/schedules and deadlines rank #1 for follow-up probability in the behavior research (estimate; behavior file ranking table, built on [S1](https://www.github.com/saraclay/Screenshot-Habits), [S6](https://www.publicstorage.com/blog/public-storage/avoiding-the-screenshot-graveyard-how-to-find-information-you-keep-saving.html)); fields are deterministically checkable; "event added unedited" is a clean metric; likely testers (students) screenshot flyers and schedules constantly.
Differentiation (press sources, not official docs; verify): Apple ships Add to Calendar only on Apple Intelligence hardware ([9to5Mac](https://9to5mac.com/2025/07/15/iphone-screenshots-are-getting-three-powerful-new-features-in-ios-26/), [TechRadar](https://www.techradar.com/phones/ios/im-a-serial-iphone-screen-shotter-and-i-cant-wait-to-use-these-3-new-features-when-ios-26-launches)); Pixel is Pixel-only. Ours: works on ordinary phones, catches the secondary deadline in the same screenshot, and shows which field it is unsure of.

## Beta features

### F1. Capture: new-screenshot detection + share/import
Auto-detect new screenshots where the platform allows (the platform decision in Round 2 determines the mechanism and limits), plus share-sheet / in-app import as the guaranteed path.
- Story: As a user, my new screenshots are noticed without me opening the app, and I can also hand any image to the app.
- Acceptance: (a) sharing or importing an image starts processing within 2 s; (b) Android: a new screenshot produces an "action ready" notification without opening the app (MediaStore trigger); iOS (cannot detect while suspended, per platform research): share sheet first, plus catch-up of new screenshots on app open (no App Intent/Back Tap in beta), and the UI says so plainly with a coached share-sheet setup step; (c) when auto-detect is unavailable or permission is limited, the app says so and offers share/import instead, never failing silently; (d) the same image is never processed twice.
- Evidence: competitor complaints 6 and 10 (import/detection failures) ([SnapSort review](https://apps.apple.com/app/id6746203579), [Captureist review](https://apps.apple.com/us/app/captureist/id6443865506)); proactive features that rarely fire are disliked ([9to5Google poll](https://9to5google.com/2025/11/18/poll-do-you-notice-google-pixels-magic-cue/)).
- Chair note: the prioritizer scored auto-watch infeasible for a non-native dev and proposed a PWA. Round 2 must decide this honestly; share/import is the floor, auto-detect is the target.

### F2. Understand: classify and extract with confidence
Classes: **event**, **deadline/to-do**, **nothing to do** (includes memes, random UI). Typed fields per class; per-field confidence; uncertain fields flagged, never guessed.
- Story: As a user, I see only what the app is sure enough to propose, and it tells me where it is unsure.
- Acceptance: (a) event proposals carry title, start (date+time), optional end, location, source (source = the "Added from a screenshot on ‹date›" notes footer written with the item; it is not a separate extracted field, D20); (b) fields that fail validation or have low confidence are visibly flagged and require review before confirm; (c) the app never invents a field absent from the screenshot (leaves blank/flagged); (d) non-actionable screenshots land silently in the library with no notification; (e) up to 3 actions can come from one screenshot (e.g., event + RSVP deadline).
- Evidence: complaint 9, extraction is a suggestion needing verification ([vendor blog](https://nemos-landing.pages.dev/blog/best-screenshot-organizer-apps-iphone), weak/competitor-authored); Apple outputs a draft the user verifies ([iDropNews](https://www.idropnews.com/?p=256322)).
- **F2(f) Printed return-date passthrough (added: purchases extension; D24).** A receipt or order screenshot that passes the sensitive guard and shows a **printed** "Return by ‹date›" / "Return window ends ‹date›" (or equivalent printed wording) is an ordinary **deadline** through the existing F2/F3/F4 path. Zero build: no new class, no Purchase action type, no retailer-policy inference, no prompt rule about returns.
  - Story: As a user, when my order screenshot says "Return by Dec 20", I get the same deadline Draft I would get from any flyer, so I don't miss the return.
  - Acceptance: (f1) the due date is grounded by source substring like any deadline (EVAL-GROUND-01); a date that is not printed is never proposed (no window is computed from a purchase date or a store policy); (f2) the year rules and the one past-date rule (D20) apply unchanged; (f3) a receipt the guard blocks stays ST-SENSITIVE ("Kept on this phone", no card, optional [Add manually]); the guard is not loosened; (f4) the card is the CMP-ACTIONCARD deadline variant with no purchase-specific UI; (f5) code (not the model) sets `deadline_origin = printed_return_by` when the grounded due-date evidence line matches the printed-return phrase list in `rules.json`, otherwise `other`; it is logged only and never changes gating; (f6) the receipt fixtures in the eval set pass the existing hard gates (DESIGN §8.1).
  - Evidence: receipts are the #2 category (S1 22/55, ±1; `raw/purchases/1_prioritizer.md`); retailer windows vary and live only in prose, so only printed dates are trustworthy (`raw/purchases/1_analyst.md` §2).

### F3. Deterministic date/time resolution
Relative dates ("tmrw 7", "this Fri") resolved by code against screenshot capture time and user timezone; missing year/timezone/AM-PM are flagged, not assumed silently.
- Story: As a user, "Friday 7pm" becomes the right Friday.
- Acceptance: test table of relative/ambiguous phrases passes (year rollover, DST, "this" vs "next", 12/24h, missing timezone); any assumption is shown on the card.
- Evidence: prioritizer scoring (reliability 5, pure code, highly testable); complaint 9.

### F4. Actions: calendar event and reminder cards
Two action types in beta. Action-ready card → edit-before-confirm sheet → execute via platform APIs (Round 2/action-engine decides destination per platform) → Undo.
- Story: As a user, I tap once to add the event or reminder after checking the fields.
- Acceptance: (a) nothing is written before an explicit tap; (b) on confirm, the created item matches the displayed fields exactly; (c) Undo within the toast window and from the history removes the created item (every history entry offers Undo EXCEPT "Sent to Calendar" (fallback, D22.6) and iOS write-only entries, "Added, can't undo from here", D7); (d) permission denial and write failure show a clear error and keep the proposal; (e) unconfirmed proposals can be dismissed without side effects.
- Evidence: calendar and reminder are the only actions any competitor ships ([competitors file §2](https://apps.apple.com/us/app/id6758023554) SnapReminder, [Captureist](https://apps.apple.com/us/app/captureist/id6443865506)); #1 follow-up category (behavior file).

### F5. Deadline alerts (MERGED INTO F4 after Round 4)
A deadline/RSVP/due date becomes ONE calendar item carrying up to 3 editable alarms (18:00 day before, 09:00 morning of, one custom). No separate Reminders permission, exact alarms or boot handling. Original text kept for traceability: rule-based reminder set shown and editable on the card.
- Story: As a user, one deadline becomes reminders that actually reach me in time.
- Acceptance: preset offsets computed in code; all offsets visible/editable; reminders never scheduled in the past; notification reliability test passes.
- Evidence: reminder reliability is a stated competitor failure ([SnapReminder release notes](https://apps.apple.com/us/app/id6758023554)); time-bound items decay fastest (behavior file implications).

### F6. Library feed + text search (lite; Round 4: FTS5 only)
Every processed screenshot appears in a feed with its class and any action state. Search is keyword (FTS5, trigram) over extracted text; search by meaning/embeddings moves to the post-beta queue (trigger: keyword search misses >20% of test queries). Acceptance (b) below applies to FTS5 with p95 ≤ 300 ms on 10k seeded items.
- Story: As a user, I can find "that flyer with the pizza night" later.
- Acceptance: (a) feed scrolls smoothly at 10,000 items; (b) keyword search (FTS5 trigram) returns relevant results over OCR text and titles with p95 ≤ 300 ms on 10k seeded items (embeddings are post-beta, queue #7); (c) results open the screenshot detail with its extracted fields and action history.
- Evidence: capture is the satisfying step, retrieval the failure ([input.sh](https://input.sh/screenshots-as-a-layer-of-interoperability), [Product Hunt thread](https://www.producthunt.com/p/unbury/do-you-have-10k-screenshots-that-you-took-to-remind-yourself-yet-u-never-check-them)); Pixel's AI search is its praised feature ([Android Authority](https://www.androidauthority.com/google-made-me-turn-off-pixel-screenshots-3680197/)).
- Chair note: the prioritizer rejected search to protect the magic moment. Kept as "lite" because the product concept, the screen list and the scale bar all require a library; if the build slips it is the last planner cut (BUILD_HANDOFF §8 item 12), taken only after every item above it (D20).

### F7. Trust and control: edit, undo, action log, privacy
Editable fields everywhere, Undo, an action history list, a plain-language statement of what leaves the device, a sensitive-content guard (banking, passwords, IDs, health, private messages: skip or keep local-only; *D1 supersedes "private messages are sensitive": chats are processed as redacted text unless the local-only toggle is on or a sensitive pattern hits*), and delete-my-data.
- Story: As a user, I always know what the app did, can reverse it, and can see what was sent where.
- Acceptance: (a) onboarding states data flow before any permission ask; (b) sensitive screens are detected and are not sent to a server and get no cloud-derived proposal; (c) history lists every executed action with Undo, except "Sent to Calendar" (fallback, D22.6) and iOS write-only entries ("Added, can't undo from here", D7); (d) user can delete one screenshot's data or all data, confirmed by a test that server copies are removed.
- Evidence: complaint 1 (silent cloud shift) ([Android Authority](https://www.androidauthority.com/google-made-me-turn-off-pixel-screenshots-3680197/), [9to5Google](https://9to5google.com/2026/06/17/pixel-screenshots-cloud-ai/)); Samsung's cloud toggle praised (same Android Authority piece); sensitive content is common in receipts/account screenshots ([S6](https://www.publicstorage.com/blog/public-storage/avoiding-the-screenshot-graveyard-how-to-find-information-you-keep-saving.html)).

### F8. Beta instrumentation (privacy-safe)
Counts only, never content: confirm rate, per-field edit rate, nothing-to-do rate, category mix, time-to-card. This feeds the eval plan and replaces the missing evidence.
- **F8 logging extension (added: purchases extension; D24).** Enum-only fields added to the `shared/` contracts **before the CP0 contracts freeze (Nov 25)**: (1) `nothing_subtype` on "nothing to do" results: `receipt_order | shipping | booking | meme | other`; (2) guard-block counts per `guard_reason` enum (plus a `receipt_like` boolean from a `rules.json` keyword list, so blocked receipts are counted without sending anything); (3) `deadline_origin` on deadline cards: `printed_return_by | other`; (4) confirm, edit and dismiss rates for deadline cards with `deadline_origin = printed_return_by`.
  - Acceptance: every new dimension is a server-validated enum; EVAL-BAR-14 still finds 0 content; the counters reconcile in the scripted 10-card session with one receipt-like nothing, one guard-blocked receipt and one printed-return deadline.
- **F8 pricing metrics (added: pricing pass); D25.** Count-only enums added to the same contracts freeze: `pro_door_event` (`view | tap_feature | dismiss`) with `pro_feature` (`backlog_sweep | purchases | expense_export | semantic_search | higher_limit | none`); `wtp_bucket` (`0 | lt1 | 1_2 | 2_4 | 4_6 | gt6`, optional); `plan_pref` (`monthly | annual | lifetime | none`); `shadow_cap_hit` (would have exceeded 30/day); `import_cap_hit` (20-image import cap reached); `usage_day_bucket` (screenshots/day `0 | 1_5 | 6_15 | 16_30 | 31+`); `search_zero_result`; `cap_tier` on cap events. No user ID, no free text; EVAL-BAR-14 still finds 0 content. They size demand for a Pro tier; nothing is for sale in the beta and the free core loop is unchanged.
  - Purpose: measures the promotion trigger for post-beta queue #1 (receipts ≥15% of processed screenshots AND ≥30% of those with a printed return date) and the guard cost of any future receipt carve-out.

### F2f. Confidence gating (minimal beta slice, added 2026-11-19; raw/5_*.md)
Each extracted field gets a score from deterministic signals (validator result, source-substring match, date-parse status, OCR line confidence, model-stated confidence); a card's score is the minimum over its required fields (title, start/due) and the class confidence; an optional field (end, location) scoring below 0.60 is cleared to `missing` and does not lower the card score (D20, matches DESIGN §5.5). Three card states using existing UI (no new screen): **Ready to add** (card score ≥ 0.90, no push downgrade), **Ask a question** (0.60 ≤ card score < 0.90; each required field in that band shows a one-line question and Add stays reachable only after the field is touched or "Looks right" is tapped), **Needs a look** (card score < 0.60 or class unsure: no push, lands in the library as "Not sure"). Hard rules: a field with no source-text match can never be "Ready"; local-only, past-date and resolve-failure items override all states. Thresholds are fixed at build time from the ~150-image eval set; the logistic (Platt-style) calibration is an OFFLINE report only in beta; user-correction data may only make the app flag MORE, never less. Alarm: if > 40% of cards land in "Ask a question", loosen only via a human-reviewed release.
- Acceptance: states render per score; no "Ready" card with an ungrounded field (hard gate, 0 violations); calibration report (ECE, reliability diagram) produced per eval run; F8 logs per-field score, signals, flagged and edited.
- Evidence: complaint 9 (extraction needs verification) and the "never invent fields" principle; the eval set supplies labels.

## Post-beta queue (in order)
1. Receipt → expense card + CSV export (second strongest category by evidence; reuses pipeline).
   - **Expanded (added: purchases extension; D24): Purchase action type, merged with receipt → expense.** Promotion trigger (from F8): receipts ≥15% of processed screenshots AND ≥30% of those show a printed return date; below that, ship expense CSV without return reminders.
   - **Slice 1: purchase extraction + return window.** Extract retailer, order number, items, prices, order and delivery dates (multi-item), every value grounded. The return-window deadline is computed **only** from a hand-curated retailer policy table: anchor (order vs delivery date), category and holiday overrides, effective date ranges, source URL, `last_verified`, stale flagging. Unknown retailer ⇒ the card asks the user ("Unknown retailer: when does your return window end?" prompt, UI.md §4.7); the model never invents a deadline. A printed return date always beats the table. Effort (analyst estimate): 3–5 days to build the top ~25 US retailers (~75–100 rules), ~2–4 h/month upkeep, plus an October holiday refresh; there is no structured or public source for retailer return policies.
     - Story: As a user, my order screenshot becomes a purchase with a return deadline I can see the rule and source for, and change.
     - Acceptance: no return deadline reaches a card without a matching non-stale policy row or a printed/user-entered date; the card shows the rule and its source; every computed deadline is user-editable; stale rows (past `last_verified` + 90 days *(est.)*, or outside their effective range) are flagged and never Ready.
   - **Slice 2: warranty end date** from user input or printed terms only (no structured manufacturer source; the US has no mandated minimum warranty, Magnuson-Moss governs disclosure only). Unranked behind slice 1.
2. Source-region highlighting on the screenshot (needs OCR boxes).
3. Teach-by-correction (explicit, viewable rules), including adaptive per-user/per-type confidence thresholds (start only after ~50 labelled outcomes per field; automatic changes may only tighten).
4. Smart resurfacing (learned action timing): per-action-type Beta priors with Bayesian updating, on-device posterior, nudge caps (2/day, 2/card, quiet hours 22–08, snooze backoff 4 h → 12 h → stop). BETA ships only the event log and a shadow-mode "would-nudge" log; NO resurfacing notifications and NO new permission prompt. Enable a fallback nudge only if F8 shows > 30% of drafts unconfirmed after 24 h. Reason: ~50–300 testers cannot train it, nudge noise risks users muting the app and killing F1's push.
5. Backlog sweep / "graveyard report" with fair batching (no hard daily cap; complaint 4).
6. Recipe → grocery list (simple append; no unit merging).
7. Search by meaning (embeddings), when keyword search misses > 20% of test queries.
8. Monetization (Pro tier) (added: pricing pass); D25: core free, Pro for power features (backlog sweep, purchases tracker, expense CSV, search by meaning, higher limit). Plan only; see DESIGN.md "Monetization plan (post-beta)" and raw/pricing/1_pricing.md. Prices, cap numbers and the Pro list wait for the F8 pricing metrics; working assumptions only: 30/day free, 100/day Pro, $3.99/mo, $24.99/yr, student $14.99/yr. Components PRICE-TIERS and PRICE-IAP, unsized.

## Rejected for beta (one line each)
- Burst/scroll stitching: merge errors undermine trust.
- Smart grocery merge: unit normalization rabbit hole.
- Auto-collections: clustering feels dumb at low volume.
- Timely resurfacing / proactive suggestions: proactive features are rarely noticed (Magic Cue, Now Brief).
- "Still want this?" decay review: needs photo-library write access; a crowded cleanup category.
- Learned personal-noise patterns: unnecessary at beta volume.
- Marketing promise of "fully on-device": not honestly achievable for beta; disclose cloud use instead.
- Purchase action type in beta, even return-window only (added: purchases extension; D24): ~4–6 sessions with no capacity (D23), conflicts with the sensitive guard, and return windows are usually not printed; beta gets only the F2(f) passthrough and F8 logging. Trigger: post-beta queue #1 promotion trigger.
- Recall matching, e.g. CPSC (added: purchases extension; D24): `ProductUPCs`/Model empty in sampled records, model/UPC mostly in free text ⇒ fuzzy matching and alarming false positives; also a proactive notification (already rejected); API terms/rate limits unstated. Revisit if purchases are live with ≥N tracked items and a vetted matching approach passes a false-positive eval.
- "Things I own" view + insurance export (added: purchases extension; D24): a different product; overlaps rejected auto-collections. Revisit if Purchase slice 1 usage shows users searching for or exporting purchases.

## Traceability table
| Feature | Primary evidence |
|---|---|
| F1 | complaints 6, 10; Magic Cue poll |
| F2 | complaint 9; Apple draft pattern |
| F3 | complaint 9; deterministic-code principle |
| F4 | competitor action coverage; #1 category |
| F5 | SnapReminder reliability; decay of time-bound items |
| F6 | input.sh and Product Hunt thread (retrieval is the failure); Pixel search praise |
| F7 | complaint 1; S6 sensitive content |
| F8 | evidence gaps listed above |
| F2f | complaint 9; "never invent fields" principle; eval-set labels |
| F2(f) printed return-date passthrough (added: purchases extension) | receipts #2 category, S1 22/55 ([1_prioritizer.md](raw/purchases/1_prioritizer.md) scores + beta passthrough); no structured return-policy source, windows vary by retailer/category/season ([1_analyst.md](raw/purchases/1_analyst.md) §2); competitors' AI-estimated deadlines ([1_analyst.md](raw/purchases/1_analyst.md) §1) |
| F8 logging extension (added: purchases extension) | "Log from day one" list and promotion trigger ([1_prioritizer.md](raw/purchases/1_prioritizer.md)); evidence gaps: no review text on missed deadlines ([1_analyst.md](raw/purchases/1_analyst.md) §1, §Takeaways 4) |
| Post-beta #1 Purchase slice 1 (added: purchases extension) | policy axes and effort estimate ([1_analyst.md](raw/purchases/1_analyst.md) §2); POST-BETA merge verdict and trust risk ([1_prioritizer.md](raw/purchases/1_prioritizer.md) "Verdict", "Trust risk") |
| Post-beta #1 slice 2 warranty (added: purchases extension) | no structured manufacturer source; Magnuson-Moss sets no minimum ([1_analyst.md](raw/purchases/1_analyst.md) §4); scored POST-BETA unranked ([1_prioritizer.md](raw/purchases/1_prioritizer.md) row b) |
| Rejected: recall matching (added: purchases extension) | CPSC fields sparse, fuzzy matching ([1_analyst.md](raw/purchases/1_analyst.md) §3); REJECT row c ([1_prioritizer.md](raw/purchases/1_prioritizer.md)) |
| Rejected: things-I-own + insurance export (added: purchases extension) | REJECT row d ([1_prioritizer.md](raw/purchases/1_prioritizer.md)); incumbents HomeTally/RecallSentry, secondary only ([1_analyst.md](raw/purchases/1_analyst.md) §1) |

## Round 2 amendments (Chair, 2026-11-18)
- F1(b) rewritten per platform research (iOS cannot auto-detect while suspended).
- F4(c) Undo on iOS requires EventKit full access; write-only is a degraded no-undo path (UI must say so).
- F7 additions: chat screenshots are processed as redacted text by default with a "keep message screenshots on this phone only" toggle; image upload for hard cases is opt-in (default off). See raw/chair_decisions.md.

## Round 4 amendments (Chair, 2026-11-19; from red team + rebuttals, see raw/4_rebuttal_*.md)
- F1(e): no screenshots from before install are processed automatically; manual imports capped at 20. No backlog in beta. Android auto-detect falls back to the iOS model (share + catch-up on open) if no working app-closed pipeline exists by end of week 2.
- F3: relative dates anchor to a day header in the screenshot when present, otherwise capture time; the anchor is shown as a tappable caption. Only missing/invalid fields block confirm; inferred year is a non-blocking caption.
- F4/F5: one calendar item with up to 3 alarms (see F5). Permissions: iOS 2 (Photos, Calendar full access for undo), Android 3 (Photos, Notifications right after, Calendar).
- F6: FTS5 only.
- F7: "Send anyway" removed; copy says names in chats are sent and makes no "not stored" claim until provider retention is verified; image upload for hard cases is default for share/import except sensitive and chat screenshots, opt-in only for auto-detected ones (amends D2); the server-copy deletion test is restated to match what is actually stored.
- Magic-moment time targets are per platform: "Reading…" card within 1 s of share; action card p50 5 s / p95 10 s end to end.
- Beta feature count is now 7 (F1, F2, F3, F4 incl. alerts, F6, F7, F8).

## Impeccable review decisions (2026-11-19; raw/4_impeccable_review.md)
- All 10 findings adopted into UI.md/BUILD_HANDOFF.md. Dates always in the clean tabular face; casual face on card titles in draft state only. An "Added" filter and swipe-undo on Home. iOS share-sheet coaching step, catch-up banner. One cross-document reconciliation table. See raw/chair_decisions.md D10–D13.

## Round 6 review amendments (Chair D20, 2026-11-19; raw/6_review_contradictions.md)
- Magic moment and F4: the Home Ready card and the Android notification both carry [Review] only; Add happens in the Confirm sheet that shows every field. Minimum path = Review, then Add (2 taps).
- F2(a): "source" is the notes footer on the written item, not an extracted field.
- F2f: card score = min over required fields + class confidence; bands Ready ≥ 0.90, Ask 0.60 ≤ s < 0.90, Needs a look < 0.60; optional fields < 0.60 → `missing`.
- F3/F4: one past-date rule. A resolved start/due in the past is a blocking date row ("This date has passed"), no push, no Ready card; Add stays blocked until a future date is picked. There is no "already happened" override. Missing AM/PM stays a non-blocking shown assumption; a weekday/date conflict and "12am" block.
- F5 (in F4): alert presets apply to deadlines only (events default to no alerts). For an all-day deadline, alerts must be ≤ 23:59 local on the due date.
- F6: search is the last planner cut (BUILD §8 item 12).
- F7: chat screenshots are detected by a deterministic on-device heuristic; "chat-uncertain" counts as chat (never image, local-only when the toggle is on). The server keeps extraction results in memory for ≤ 10 min only; Postgres holds no content.
- **Conditional amendments (apply only if the named BUILD §8 cut is taken; each needs a Chair note at the time):**
  - Cut 6 (on-device shadow evaluator): amends post-beta queue #4's "shadow-mode would-nudge log" to "behavior_event log only"; D18's shadow metrics are then computed post-beta from the retained on-device rows.
  - Cut 7 (calibration report detail): F2f acceptance is NOT amended; the reduced report still contains ECE and a 5-bin reliability table, and still freezes thresholds. Only the Platt fit, per-type/per-field breakdowns and plotted diagrams are dropped (D18's per-type/field reliability becomes pooled).
  - Cut 11 (iOS catch-up): amends F1(b) iOS to "share sheet + in-app import only" and drops the iOS catch-up half of EVAL-BAR-12; F1(c) copy still says so plainly.

## Change log
- 2026-11-18: locked. Chair deviations from prioritizer: kept lite search (F6), framed capture as auto-detect with share/import floor (F1) and left platform choice to Round 2.
- 2026-11-19 (added: purchases extension; D24): F2(f) passthrough and F8 logging extension added (zero build, no new feature, beta feature count stays 7); post-beta queue #1 expanded into the Purchase action type (slice 1 return window from a policy table, slice 2 warranty); recall matching and "things I own" rejected with revisit triggers. The core loop, magic moment and beta scope are unchanged.
