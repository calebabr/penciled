# Session start prompt: SPR-01 (paste into a fresh Claude Code session in C:\dev\screenshot-actions)

```
You are continuing the Penciled beta build. Session 1 of sprint SPR-01: Monorepo and
dependency matrix (session 1 of 1). Work only on this sprint's components (COMP-REPO, including spike SP-13).

READ FIRST (in order, nothing else unless a detail is missing):
1. CLAUDE.md and STATUS.md (root): rules, board, builder checklist, toolchain notes.
2. docs/SPRINT_PLAN.md: the SPR-01 entry, §4 session template, §5 cut triggers.
3. docs/BUILD_HANDOFF.md §1.3, §1.4 (repo layout), §1.7 (hard rules) and the COMP-REPO entry in §2.
Run `git status`, `git log -5 --format='%an %ae %s'` first.

DO:
- Scaffold apps/mobile (Expo, pinned SDK, dev client profile, EAS profiles), server (FastAPI
  skeleton), shared, eval, tools, and CI per the Exit criteria. Write tests first where the Exit line names one.
- Run SP-13: one dev build per platform boots and calls expo-sqlite, the RN ML Kit wrapper, FlashList v2,
  Reanimated, expo-share-intent, expo-calendar, expo-media-library, expo-secure-store and the fonts.
  Record the Node-version finding (Node 24 installed) and the pinned SDK in docs/spikes/SP-13.md.
- CI: lint, typecheck, Jest, pytest, a secret scan that fails on a planted fake key, an ESLint rule that
  fails on a raw hex in src/ui, and a no-content-log grep job. Metro on Windows must drive both phones.
- App name: Penciled. Propose bundle ID, URL scheme and iOS App Group ID based on the builder's developer identity and ask the builder to confirm them before writing them to app.config.ts.
- No Swift. If the ML Kit wrapper fails on iOS new arch, use the listed fallbacks and escalate to the Chair on day 2.
- Stop at ~4.5 hours or when Exit passes.

HARD RULES: see CLAUDE.md (never log content, never read or commit .env or secrets, tokens only in UI,
commit as the configured identity with no AI attribution, no push unless asked).

LEAVE: tests green; root STATUS.md updated (sprint board, sessions used vs plan, blockers, exact "Next:" line);
CLAUDE.md refined if needed; docs/spikes/SP-13.md; .gitignore covering .env*; one commit per coherent step,
message "SPR-01 <component>: <what>".
Reply with: Exit criteria passed/failed, sessions used, next step.
```
