# CLAUDE.md: project rules (read first, every session)

Project: screenshot-to-action mobile app (working title: Screenshot Actions; final name pending, must be chosen before SPR-01 sets bundle IDs). A new screenshot becomes a proposed calendar action; the user reviews and taps Add. Stack: Expo / React Native (TypeScript) app, thin Kotlin Android worker, FastAPI server, shared JSON-schema contracts. Beta target: testers install Jan 13–15, 2027.

All design lives in `docs/`:
- `docs/BUILD_HANDOFF.md`: components, acceptance criteria, hard rules (§1.7), repo layout (§1.4), cut list (§8).
- `docs/SPRINT_PLAN.md`: ordered sprints (SPR-01..33), calendar, session prompt template (§4), cut triggers (§5).
- `docs/FEATURES.md`, `docs/UI.md`, `docs/DESIGN.md`, `docs/SPRINT_IMPACT.md`; raw notes and decisions in `docs/raw/` (`chair_decisions.md` is authoritative; later decisions win).

## Session protocol
1. Read root `STATUS.md` ("Next" line), then your sprint's entry in `docs/SPRINT_PLAN.md` and the BUILD_HANDOFF entries for its components. Use `docs/SESSION_START.md` as the opening prompt.
2. Run `git status`, `git log -5`, and the test suites before new work.
3. Work only inside the sprint's lane/files. Stop at ~4.5 hours or when the Exit criteria pass.
4. Before ending: tests green (or the failing test named in STATUS), component `STATUS.md` updated, root `STATUS.md` updated with sessions used vs plan and an exact "Next:" line, one commit per coherent step.

## Hard rules (never break)
- The model never executes an action. Code validates. A calendar write happens only from a user tap on Add in the Confirm sheet. Cards and notifications carry [Review] only.
- Never log screenshot content (OCR text, images, extracted fields, model output, request bodies) anywhere.
- Sensitive screenshots, chat screenshots with the local-only toggle on, and a missing `worker_config` mean zero network requests.
- Never read, print or commit `.env` files, API keys, signing keys or other secrets. Do not open `.env*` files at all.
- UI uses `src/theme.ts` tokens only: no raw hex, no inline numeric styles.
- Date maths happens only in the server resolver. Prompts and thresholds change only through a human-approved baseline-bump commit.
- Shared contracts (`shared/`) are frozen at CP0 (Nov 25); changes need a version bump and a note.
- No Swift. iOS builds go through EAS cloud builds only (builder is on Windows, no Mac).

## Git rules
- Commit only as the configured identity: `calebabr <cjabrantes06@gmail.com>`. Check `git config user.name` and `user.email` first.
- Never add `Co-Authored-By`, "Generated with Claude Code", or any AI attribution to commits, PRs or tags.
- Never push unless the builder asks in that session. There is currently no remote.
- Commit message format: `<SPR-xx> <component>: <what>`.
