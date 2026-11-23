# Pending: final end-to-end read-through (paused 2026-11-19 at 88% usage, per user)

State: all four deliverables written; review fixes (D19, D20, D21 in chair_decisions.md) applied. The read-through agent was stopped within its first minutes; it may have made a few mechanical edits, none verified.

When resuming, run one opus reviewer to read FEATURES.md, UI.md, DESIGN.md, BUILD_HANDOFF.md end to end and check:
1. leftovers of old behavior (notification [Add], NTF-ADDED, one-tap Add from Home card, "PM?" flag, "memory only" vs database storage, result_json in Postgres, 6 s toast, SCR-GALLERY/DETAIL/HISTORY as screens, embeddings in beta, Reminders permission, App Intent/Back Tap, "Send anyway", tester counts);
2. every referenced ID exists; every UI.md ID maps to a BUILD_HANDOFF component;
3. numbers agree (0.90/0.60, 18:00/09:00, 8 s toast, $25 cap, latency, 300 ms search, cost per 100);
4. no component above L; size counts, session total and critical path add up; graph matches dependencies (COMP-CALIB before COMP-GATE);
5. new contradictions or broken tables from the ~170 edits;
6. model never executes; every action needs a tap; no content logging; no secrets.
May fix mechanical issues directly; list design decisions for the Chair. Report to raw/6_final_readthrough.md (≤900 words), including whether BUILD_HANDOFF.md is self-contained.
