# apps/mobile STATUS

**Component:** COMP-REPO (mobile side) incl. SP-13 · **Sprint:** SPR-01 · **Updated:** 2026-11-23

Pinned: Expo SDK 58 (`expo` 58.0.26), React Native 0.88.1, React 19.3.0, Node 24.13.0 supported. Full matrix and findings: `docs/spikes/SP-13.md`.

## COMP-REPO accept lines (mobile side)

- [x] Expo app scaffolded: TypeScript, Expo Router (`app/`), New Architecture (the only architecture on SDK 58), exact-pinned deps via `npx expo install`.
- [x] Store identifiers in `app.identity.ts` (CONFIRMED by builder 2026-11-23): `app.penciled` (iOS + Android), scheme `penciled`, App Group `group.app.penciled`.
- [x] `eas.json` profiles: development (dev client, internal), preview (internal), production. No secrets.
- [x] `src/theme.ts` token stub (UI.md §7.2 palette light/dark, space, radius, border, type, motion).
- [x] ESLint fails on a raw hex in `src/ui` (custom rule `eslint-rules/no-raw-style-values.js`, scoped to `src/ui/**` and `src/features/**`; Jest test proves fail on hex / pass on token).
- [x] Root scripts green: `npm run lint`, `npm run typecheck`, `npm test` (2 suites, 21 tests).
- [x] `npx expo-doctor` 20/20; `npx expo prebuild --no-install --platform android` resolves all config plugins.
- [x] `/sp13` dev-only smoke screen probes all SP-13 libraries; results on screen only, content-free.
- [ ] **Builder-pending:** EAS dev build boots on a physical Android phone (`docs/spikes/SP-13.md` §7).
- [ ] **Builder-pending:** EAS dev build boots on a physical iPhone (needs Apple Developer membership; first iOS build also creates the App Group).
- [ ] **Builder-pending:** Metro on Windows drives both phones; `/sp13` results recorded in `docs/spikes/SP-13.md` §8.
- [ ] CI green on an empty PR (owned by the CI lane: `.github/workflows/`; it calls the root `lint` / `typecheck` / `test` scripts).

## Open items

- Recursive **Casual** statics are not in `@expo-google-fonts/recursive`; make Casual 600 with fonttools in the theme sprint (UI.md §2.2).
- Review Android permissions `WRITE_EXTERNAL_STORAGE` and `SYSTEM_ALERT_WINDOW` before store builds.
- After `npx eas-cli init`, add `extra.eas.projectId` to `app.config.ts`.
- If ML Kit wrapper fails on a device build: fallbacks in `docs/spikes/SP-13.md` §4; escalate iOS failure to the Chair on day 2.

## Next

Builder runs SP-13 §7 (EAS login, dev builds, `/sp13` on both phones) and fills in §8.
