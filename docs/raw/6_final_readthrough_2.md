# 6. Final read-through 2 (after D22)

Scope: FEATURES, UI, DESIGN and BUILD_HANDOFF, read end to end against D1–D22. Design only; nothing built or run.
Counts: **6 mechanical fixes** · **4 remaining issues (1 P2, 3 P3)** · **42 "verify" claims**.

## Checks that passed
1. **D22 is applied in all four documents, and their structure is intact.**
   - .1: COMP-GATE Depends/Accept, the graph edge `CALIB -.->|threshold freeze| GATE` (valid Mermaid), §3 and §6.
   - .2: $3–8 in DESIGN §4.5 and §5.8 and in BUILD §5.
   - .3: FEATURES F7 note.
   - .4: DESIGN Q2.
   - .5: DESIGN §7.2.
   - .6: DESIGN §6.5, UI ST-PERM-CAL-DENIED and BUILD EXECUTOR Accept.
   - Tables, Mermaid and section numbering are intact.
2. **The numbers add up.**
   - Components: 25 S + 14 M + 0 L = 39, and 53 sessions. Both name lists match.
   - The critical path sums to 20.
   - GATE ends at about session 7 and CALIB at about session 9, both before RC.
   - All checkpoint weekdays and dates are correct.
3. **No stale phrases.** Each phrase on the check list appears only as a negation or in a reconciliation row. "Added (can't undo)" is now used only for the iOS write-only path.
4. **IDs map.** Every UI.md ID maps to a component in BUILD §2.10.
5. **Files are clean.** All four use LF only, with no BOM and no mangled characters.
6. **The hard rules hold.**
   - The model has no tools.
   - Writes happen only from Add in the sheet. Cards and notifications offer [Review] only, and reconcile needs a fresh tap.
   - No content goes into logs, 422 bodies, Postgres or F8.
   - Secrets are only in the host store and EAS env.
   - Rule 12 matches the git rule.
   - BUILD §1.2 matches the FEATURES acceptance criteria.

## (a) Fixes made
1–3. The authority lines in UI, DESIGN and BUILD now read D1–D21 → D1–D22.
4. DESIGN §3.1: "CALIB before GATE" is now a soft threshold-freeze edge (D22.1). It previously read as a hard dependency.
5. BUILD COMP-CALIB: added "(soft 'threshold freeze' edge only, D22.1)".
6. UI §7.8: new reconciliation row 46 for D22.6.

## (b) Remaining issues
1. **P2: Nothing places COMP-GATE before CP2.** GATE's only outgoing edge goes to RC. But the CP2 frames A1 and I3 need real `gate_state` values (NTF-CHECK and the Ask card), so a planner could legally schedule GATE after CP2.
   **Rec:** add `GATE --> CONFIRM`, or put "GATE done" in the CP2 row. GATE ends at session 7 and CONFIRM starts at session 8, so the critical path stays at 20.
2. **P3: "Sent to Calendar" is missing from the UI vocabulary table and from §4.4 History.** Today those define only Added, Undone and Released.
   **Rec:** add it to both, with "no Undo".
3. **P3: FEATURES F4(c)/F7(c) promise Undo for every history entry.** The fallback path (Sent to Calendar) has none. The Round 2 amendment covers only write-only.
   **Rec:** add a one-line FEATURES amendment citing D22.6.
4. **P3: DESIGN Q2 reads as contradictory.** It says internal TestFlight "cannot cover" 50 testers, yet falls back to internal (max 100). The real limit is that each tester must be an App Store Connect team member.
   **Rec:** reword.

## (c) "verify" markers (claim covered)
**FEATURES (1):** the Apple/Pixel differentiation press sources.

**UI (14):**
- the React Native Increase Contrast API
- Recursive Casual statics (×2)
- tabular-nums
- gorhom focus issues (SP-14)
- M3 easing values
- Apple haptics claim
- Android haptics mapping
- predictive back
- M3 snackbar link
- formSheet Android parity
- one Calendar prompt (SP-8)
- formSheet option names
- Material Symbols Rounded

**DESIGN (19):**
- the link convention
- the expo-share-intent URL
- the EAS Submit link
- the EAS free quota
- TestFlight and Play limits
- FlashList v2 notes
- ML Kit on the new architecture
- iOS backup exclusion for index.db
- the $25 console cap
- the content-URI re-enqueue
- ITPM/OTPM
- cache reads vs ITPM
- the cache prefix minimum
- FTS5 trigram in expo-sqlite
- expo-calendar alarm types
- the Android Reminders link
- `calshow:`
- the org-retention article
- Maestro on iOS

**BUILD (8):**
- the convention
- EAS env-var naming
- `eas build --local` on Windows
- the EAS quota
- the SP-16 runner
- Apple holiday dates (CP3 and Dec 18–21)
- store tester limits
- identity-verification time

**Verdict:** Ready for sprint planning once (b)1 is fixed by adding one graph edge. The rest is cosmetic.
