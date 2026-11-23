# 4 — Impeccable critique: UI material to date (design review only)

Method: design review only (detector not applicable, native platform). Surface mode: Operate. Platform: adaptive (Expo/React Native on iOS + Android). Reviewed on paper: raw/2_ui.md, raw/4_rebuttal_ui.md, raw/4_design_brainstorm.md, UI-facing parts of raw/3_eval.md, raw/2_actions.md, raw/2_privacy.md, FEATURES.md. Nothing rendered; no PRODUCT.md exists (offer `/impeccable init` at build time). Contrast figures are estimates.

## Design Health Score

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of System Status | 3 | Processing steps, toast, history are good; iOS has no "action ready" signal at all (share-only), so status after sharing relies on the skeleton |
| 2 | Match System / Real World | 3 | Pencil→ink is a real-world metaphor; "proposal / draft / ready" vocabulary drifts |
| 3 | User Control and Freedom | 3 | Undo + discard + edited-event guard are strong; History (the undo home) is buried in Settings |
| 4 | Consistency and Standards | 2 | Documents contradict each other (ONB-2 copy, QA-SNAP tooling, 6s/8s toast, chips vs alerts); custom type on core data |
| 5 | Error Prevention | 3 | Blocking vs assumption flags, past-date chips disabled; disabled Add gives no reason on the button |
| 6 | Recognition Rather Than Recall | 3 | Screenshot beside every field is excellent; iOS share-extension discovery is recall-heavy |
| 7 | Flexibility and Efficiency | 2 | Single-item flow only; no multi-select, no quick-add from the notification when flags exist, iOS has one entry path |
| 8 | Aesthetic and Minimalist Design | 3 | Strong restraint; ONB-3 overloaded |
| 9 | Error Recovery | 3 | Plain-language failures that keep the user's edits |
| 10 | Help and Documentation | 2 | Only "Learn more"; no coaching for share-sheet setup or limited photo access |
| **Total** | | **27/40** | **Acceptable (67%): solid concept, execution gaps to close before build** |

## Design specificity verdict
The original "quiet paper + one ink" (2_ui.md) is category-interchangeable: stock Tailwind indigo/amber/green, system font, one radius and shadow on everything. The frontend-design revision ("Pencil, highlighter, ink") is authored for this product: pencilled draft to inked commitment is the idiom for tentative vs committed calendar entries. The tension to resolve: the doc's own principle is "precise and restrained, not sparkly", while a handwriting-leaning face (Recursive Casual) sits on the most trust-critical data, the date.

## What's working
1. Draft-until-you-tap as a visual state (dashed to solid) makes the core safety principle visible; it is the best idea in the set.
2. Source thumbnail beside every field, one flag with a reason, two flag tiers (blocking vs assumption).
3. Honest edge states: offline, limited photos, sensitive, server error; accessibility labels written per card; undo guarded when the user edited the event afterwards.

## Priority issues
1. **[P1] Recursive Casual on dates/times.** Brainstorm sets dates in Casual while draft. Handwriting-style digits (1/7, 5/6) at AX sizes undermine the exact thing the user is verifying. Fix: Casual for card title only; date line stays Linear with tabular figures in both states; the draft is signalled by the dashed border and the "Draft" label. Test both fonts at 200% before committing. Command: /impeccable typeset.
2. **[P1] Undo has no home.** Rebuttal folds History into Settings and removes the tab bar. Undo is the trust mechanism and the toast lasts 8 s. Fix: an "Added" filter chip on Home (same grid, inked-tick tiles) and a long-press/swipe Undo on added items; Settings keeps the log. Command: /impeccable layout.
3. **[P1] iOS entry path is undesigned.** iOS = share sheet + catch-up on open, but nothing teaches enabling the app in the share sheet (it hides under "More"). Jordan abandons at step one. Fix: a dedicated ONB step with a real-screenshot walkthrough of adding the app to Favorites, a Home empty state that repeats it, and a catch-up banner ("3 new screenshots, Read them"). Command: /impeccable onboard.
4. **[P1] Documents conflict; the build will inherit them.** 2_ui ONB-2 still says "Nothing is saved on the server" (rebuttal: no claim until D3 verified; names in chats are sent). 3_eval QA-SNAP still specifies pixel diffs/Storybook/Detox, SCR-DETAIL history, and a 500 ms Confirm budget that the 680 ms ink-in violates. 2_ui chips say "Reminder ladder", rebuttal says alerts. Fix in Round 5: one reconciliation table. Command: /impeccable clarify.
5. **[P2] Disabled primary button without a reason.** "Add disabled until flags resolved" leaves a dead control. Fix: keep the button enabled-looking and make it scroll to and highlight the first blocking flag, label "Check year to continue".
6. **[P2] Ink-in vs reality.** Define that the calendar write starts at tap, the animation never gates it, and a failed write plays a reverse (card returns to draft with the error banner). Split QA-PERF-04 into tap-to-write-started ≤ 500 ms and animation ≤ 700 ms.
7. **[P2] ONB-3 does three jobs** (try-it, Photos, Notifications on Android). One decision per screen: split Notifications onto its own screen after the sample succeeds.
8. **[P2] Platform conformance gaps.** No Android navigation/back spec (system Back must dismiss the confirm sheet, with a dirty-state guard); no Dynamic Color decision (brand wins, but state the static scheme); bottom-sheet library has known screen-reader focus issues, so prefer Expo Router's native formSheet; tokens are raw hex with no Increase Contrast set after the rebuttal cut it; "Toast" should be "snackbar" on Android.
9. **[P2] Vocabulary.** Proposal / draft / ready / suggestion all appear. Choose "Draft" (state), "Ready to add" (section), "Dismiss" (not "Discard proposal").
10. **[P3] Thumbnail assumes 9:19.5.** Use cover-crop with a fixed 6 pt radius for any aspect; pre-generate small thumbnail files at ingest or the 10k grid will decode full-size images.

## Persona red flags
- **Jordan (first-timer):** iOS user finishes onboarding and cannot find the app in the share sheet; "Looks right" is unexplained; Add is disabled with no reason.
- **Casey (distracted mobile):** Undo toast gone in 8 s and History is two taps deep in Settings; Notifications asked straight after Photos on Android.
- **Sam (accessibility):** Casual-font digits at 200%; bottom-sheet focus trap; toast Undo timing needs the pause-on-focus rule; dashed-vs-solid thumbnail status relies on shape alone at thumbnail scale (badges must stay in the accessibility label).

## Minor observations
Highlighter yellow is also the dark-mode text color on a dark brown fill, so check non-text contrast of the 3 pt mark; destination-color dot needs a non-color name beside it; "Nothing to do" items need a way to be un-ignored.

## Questions to consider
Does the product want to feel like a careful assistant or a friendly notebook? Would the date line be more trusted set in the quietest type in the app? What if History were the inked view of Home rather than another list?

## Recommended actions
1. /impeccable typeset: dates in Linear; Casual only on titles; test at 200%.
2. /impeccable layout: Added chip on Home, swipe-undo, enabled "Check year" button behavior.
3. /impeccable onboard: iOS share-sheet coaching step, split ONB-3, catch-up banner.
4. /impeccable clarify: vocabulary and the cross-document reconciliation list.
5. /impeccable adapt: Android back/insets/Dynamic Color decision, native formSheet.
6. /impeccable polish: final pass once screens exist.
