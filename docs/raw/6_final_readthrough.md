# 6. Final read-through (FEATURES → UI → DESIGN → BUILD_HANDOFF)

Scope: all four deliverables read end to end against D1–D21 and raw/6_review_contradictions.md. Design only; nothing built or run.
Counts: **17 mechanical fixes** · **6 Chair items (0 P0, 0 P1, 1 P2, 5 P3)**.
Note: the interrupted earlier pass left no detectable stray edits. Every passage read is consistent with D19–D21 except the items below.

## Checks that passed
- **Leftovers:** no notification [Add], no NTF-ADDED (only in the reconciliation "removed" rows), no one-tap Add from a card, no "PM?" blocking flag (only reconciliation #41), no `result_json` column (DESIGN §3.4 says "no result column"), no 6 s toast, no Gallery, Detail or History screens, no embeddings or sqlite-vec in the beta, no Reminders permission, no App Intent or Back Tap, no "Send anyway". Tester count is 50 expected and 300 ceiling everywhere.
- **Numbers:** 0.90/0.60, 18:00/09:00 (all-day bound 23:59), 8 s toast, $25/month cap, 100/day, p50 5 s / p95 10 s, ≤1 s Reading card, ≤2 s processing start, 300 ms search at 10k, ≤500 ms tap-to-write and ≤700 ms ink-in, and $0.002 mean per screenshot (= $0.20 per 100) all agree. Weekdays in the examples are correct for 2026/27.
- **Sizes:** 25 S + 14 M + 0 L = 39 components, 25 + 28 = 53 sessions. Both totals match the component list. Critical path 1+1+2+1+1+2+2+2+1+1+2+1+2+1 = 20 ✓.
- **Graph:** CALIB → GATE is present. Every *Depends* edge is in the graph directly or transitively, except one, fixed below.
- **Coverage:** every UI.md screen, ONB, CMP, NTF, ST, A11Y, MAE and frame ID maps to a component in BUILD §2.10.
- **Safety:** the model has no tools. Every write needs Add in the sheet, and reconcile never writes after a relaunch or after 8 s. No content goes into logs, 422 bodies, F8 or behavior_event. Secrets are only in the host store and EAS environment variables. Rule 12 matches the builder's git rule.

## (a) Fixes made
**UI.md**
1. Sources line: D1–D20 → D1–D21.
2. CMP-BADGE: added the "Past date" badge (D21.2).
3. ST-PAST: Library tile shows the "Past date" badge and is counted in F8 (D21.2).
4. ST-ALREADY-ADDED: Add in the sheet first shows a CMP-DIALOG "Add again?" (D21.4).
5. Reconciliation #7: the stale "Check year/time to continue" now reads "Check … to continue (e.g. date)". Year and time are no longer blocking.
6. §7.7: added cut 0, the Increase Contrast set (D21.5).

**DESIGN.md**
7. Precedence line: D1–D20 → D1–D21.
8. §1 summary: "adds with one tap" now names the Review → sheet → Add path (D19/D20).
9. §5.4 past rule: "Past date" badge and the F8 count (D21.2).
10. §3.6: COMP-RESOLVER now maps to BUILD's COMP-RESOLVER-DATE and COMP-RESOLVER-GVP. Before, the ID had no matching component.

**BUILD_HANDOFF.md**
11. Status line: D1–D20 → D1–D21.
12. CP2 iOS path: "card → Add" → "card → Review → Add".
13. COMP-UI-A11Y: custom actions now read "card: Review/Dismiss/Undo; Add only in the sheet".
14. Coverage table: ST-PAST gains COMP-UI-HOME (badge) and COMP-METRICS (count). ST-ALREADY-ADDED gains COMP-UI-CONFIRM ("Add again?").
15. COMP-METRICS: past-date counter added.
16. Graph: added the missing CONTRACTS → UI-LIB edge. HOME, READONLY, SETTINGS and ONBOARD now carry a "*Sequenced after* …" note, so the four screen-order edges in the graph match the component entries.
17. Increase Contrast (D21.5): conditional note on COMP-UI-THEME and new cut 0 in §8. The references "from item 1" (§0) and "cuts 1–7" (§9) now say item 0 and cuts 0–7. Existing numbering is unchanged.

## (b) Needs a Chair decision
1. **P2: COMP-GATE dependency is self-contradictory.** GATE depends on CALIB, which comes at the end of the eval chain (about session 10), yet its purpose says it "starts from initial constants until COMP-CALIB freezes them". Nothing upstream of PIPELINE or UI-CONFIRM depends on GATE, even though CP2 needs real `gate_state` values from the server. **Rec:** build GATE code after GVP only (before PIPELINE). Make "thresholds_v1 frozen" a separate CALIB → RC milestone. This keeps D18 (calibration before the thresholds the gate ships with).
2. **P3: beta cost basis.** DESIGN §4.5 gives "≈$6–8/month" for 50 testers. That only holds if every tester is active daily; at the stated 50% DAU it is about $3–4. **Rec:** keep $6–8 as the conservative figure and add "assumes all testers active".
3. **P3: FEATURES F7 base text** still lists "private messages" as sensitive (skip or local-only). D1 superseded this, and only the Round 2 amendment says so. **Rec:** add an inline "(superseded by D1)" note. F7 is locked text, so I did not edit it.
4. **P3: DESIGN Q2.** The FAIL branch says "stay internal", but §2.2 says internal TestFlight is limited to team members, so 50 testers need external. **Rec:** FAIL = revise and resubmit, with an Android-first beta until approval.
5. **P3: undefined post-beta IDs.** SEC-AUTH-FUTURE, SEC-DEL-ACCT and SEC-EXPORT are referenced but never defined. **Rec:** add one line each to DESIGN §7.2 marked post-beta.
6. **P3: ST-PERM-CAL-DENIED [Open in Calendar]** logs "Added (can't undo from here)", but the app cannot know whether the user saved in the system editor. **Rec:** log it as "Sent to Calendar (can't undo from here)".

## (c) Is BUILD_HANDOFF.md self-contained for a sprint planner?
**Yes.** A planner needs nothing else to plan from it. It has:
- every component, with size, risk, dependencies and checkable acceptance
- matching size totals and a critical path that adds up
- the dependency graph
- spike order with pass/fail
- dated checkpoints and lead-time tasks
- parallel lanes with file ownership
- pre-beta gates, a numbered cut list with savings, a buffer, and known unknowns

Cross-references to DESIGN and UI sections (e.g. DESIGN §5.2, §5.5, UI §4.x) are pointers for the builder, not inputs the planner needs. The one planning-relevant gap is item (b)1: as written, the planner would schedule COMP-GATE after the eval chain, leaving PIPELINE and CP2 without server gate states. Resolve that before sprint planning.
