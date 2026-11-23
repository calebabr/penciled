# STATUS.md (root): update at the end of every session

**Current sprint:** none started. Next: **SPR-01 Monorepo and dependency matrix** (1 session, W1).
**Last green commit:** docs only (initial design import). No code exists yet.
**Sessions used vs plan:** 0 used / 53 planned (baseline 7 sessions a week).
**Cuts taken:** none. Cut triggers T0–T4 are in `docs/SPRINT_PLAN.md` §5.
**Gate results:** Dec 2 Android worker gate (SP-2): not run. SP-3 (iOS share extension opens app): not run.
**RB1 / store status:** not started.

## Next
SPR-01. Open a fresh session and paste `docs/SESSION_START.md`. Before that, finish the builder checklist below, especially the app name.

## Builder checklist (things only you can do; tick when done)
- [x] App name chosen: **Penciled** (2026-11-23). Still to do: check availability in both stores and as a domain before SPR-01 sets bundle IDs, and confirm the bundle ID, URL scheme and App Group ID in SPR-01 (alternatives if taken: Pencil In, Inked, Shotlist, Snapdone).
- [ ] Apple Developer Program enrolment (paid; can take days to approve). Needed for TestFlight and the share extension App Group.
- [ ] Google Play Console developer account (paid once; identity verification can take days).
- [ ] Expo account (free) for EAS builds; log in with `npx eas-cli login` when SPR-01 asks.
- [ ] LLM provider account with a paid-tier key. Store it as an environment variable or a secret manager entry. Never write it to a file the repo can see, and never paste it into a session.
- [ ] A physical iPhone and a physical Android phone for dev builds (simulators can't prove the share sheet or background behavior).
- [ ] GitHub account decision: create a private repo and push when you choose (no remote exists; the repo is the only copy of the project docs).
- [ ] Hosting account for the server (decided in SPR-04; a free-tier container host is planned).

## Local toolchain (checked 2026-11-23)
Found: Node 24.13.0, npm 11.6.2, Python 3.11.9, Java 17 (Temurin), Git 2.52.0.
Missing: `eas-cli` (run via `npx`), Android `adb`/platform-tools, `gh`.
Not yet verified: whether the Expo SDK that SP-13 will pin supports Node 24 (SPR-01 records the answer; install an LTS Node alongside if it does not).

## Sprint board
See `docs/SPRINT_PLAN.md` §2 and §3. Update this file's header lines each session.
