# apps/mobile STATUS

**Components:** COMP-REPO (mobile side) incl. SP-13 (SPR-01); COMP-STORE app config and COMP-SHARE-IOS slice A / SP-3 spike (SPR-03) · **Updated:** 2026-11-23

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

## SPR-03: store pipeline and share-extension spike (app-config half)

### Configured (desk-verified on Windows)

- **expo-share-intent 9.0.0** (`app.config.ts`): iOS activation = images only, `NSExtensionActivationSupportsImageWithMaxCount: 1` (a share is one screenshot; bulk goes through the 20-image import, F1(e)). App Group `group.app.penciled` from `app.identity.ts`. Extension target `ShareExtension` with bundle ID **`app.penciled.share-extension`** (derived from `identity.iosBundleId`, set explicitly; nothing assumes `.ShareExtension`). Android `ACTION_SEND` `image/*` only, **no `SEND_MULTIPLE`** (matches iOS MaxCount 1). The plugin writes `extra.eas.build.experimental.ios.appExtensions` itself so EAS provisions the extension; do not add that block by hand (the plugin throws on a duplicate).
- Removed the `ios.entitlements` App Group from `app.config.ts`: the plugin already adds it, and both together produced a duplicate array entry.
- **`iosHideView: true`** (plugin default, now explicit). **First fallback** if the source app freezes after a share in a release build (expo-share-intent #217 / #231, reproducible from the share sheet "More" list; #243 SIGTRAP crash is separate): set `iosHideView: false` (a modal flashes, then the app opens). Native change, needs a new EAS build. Next fallback per BUILD_HANDOFF: "Saved. Open the app to review." / `expo-sharing`.
- `ios.config.usesNonExemptEncryption: false` (`ITSAppUsesNonExemptEncryption = NO`; HTTPS only) so TestFlight uploads skip the export-compliance stall.
- **Version policy:** `version` stays **0.1.0** through the RC; only the build number moves (`appVersionSource: remote` + `autoIncrement` on `production`). A new marketing version would trigger another Beta App Review for external TestFlight.
- **Android permissions (store builds):**
  - `WRITE_EXTERNAL_STORAGE` (maxSdk 32) is merged in by expo-media-library and expo-file-system although we never save media → `android.blockedPermissions` (`tools:node="remove"`).
  - `SYSTEM_ALERT_WINDOW` comes from the prebuild template's *main* manifest and, separately, from the `src/debug` and `src/debugOptimized` manifests (React Native dev overlay). `plugins/withReleasePermissionTrim.js` deletes only the main-manifest line, so debug / dev-client builds keep it and release builds drop it. (Not `blockedPermissions`: its remove marker in the main manifest could interfere with the debug declaration.)
  - Kept: `INTERNET`; `READ/WRITE_CALENDAR` (executor); `READ_MEDIA_IMAGES` + `READ_MEDIA_VISUAL_USER_SELECTED` (screenshots, Android 13/14 partial access); `READ_EXTERNAL_STORAGE` maxSdk 32 (screenshots on Android ≤12); `VIBRATE` (haptics).
  - Verified in the prebuild output: main manifest has no `SYSTEM_ALERT_WINDOW` and has `WRITE_EXTERNAL_STORAGE tools:node="remove"`; the debug manifest still has `SYSTEM_ALERT_WINDOW`. **Not** verified through a Gradle manifest merge (no Android SDK here): check `aapt dump permissions` on the first release AAB/APK.
- **`eas.json` submit `production`:** `ios: {}`. No `ascAppId` / `appleId` / `appleTeamId` (no fake values): `eas submit` prompts, can create the App Store Connect record, and the builder adds `ascAppId` afterwards if wanted. `android: { track: "internal", releaseStatus: "draft" }`: `draft` is required while the Play app itself is still a draft; switch to `completed` after the first manual release. **No `serviceAccountKeyPath`**: upload the Google service-account JSON to EAS (`eas credentials` → Android → Google Service Account Key) so no key file lives in the repo (`service-account*.json` is git-ignored anyway). No separate `preview` submit profile: TestFlight internal + Play internal is exactly what `production` does; `preview` builds stay internal distribution.
- **SP-3 spike screen** `/share-spike` (`app/share-spike.tsx`, `src/features/sharespike/`): enabled when `__DEV__` **or** the JS was built with `EXPO_PUBLIC_SHARE_SPIKE=1` (`gate.ts`), so timing can be taken on a release / TestFlight build without Metro; builds without the flag redirect home. `ShareSpikeRouter` (root layout) records each share: receipt time vs JS start (cold) or vs the last `AppState` active (warm), sanitised MIME type, file count, readable (file exists with size > 0, expo-file-system); then navigates to `/share-spike`, which shows a "Reading…" card whose layout (+1 frame) is the "Reading visible" time. Samples persist in `expo-sqlite/kv-store` (timings, MIME, flags only) and render as a selectable tab-separated table for `docs/spikes/SP-3.md`. No content, names, paths, network or console output. Native launch time before the JS bundle starts is **not** measured: time tap-to-app-open with a screen recording.
- `app/+native-intent.tsx`: rewrites the iOS `penciled://dataUrl=…` open URL (otherwise "Unmatched route") to `/share-spike` (spike builds) or `/` (store builds).
- `expo-file-system` 58.0.14 is now a direct dependency (it was already in the binary through `expo`; no native change).
- Jest: `src/features/sharespike/__tests__/stats.test.ts` (timing, percentile, table logic).

### Needs the builder (in order)

1. Apple Developer Program enrolment (identity verification) and a Play Console account.
2. `npx eas-cli login`, then `npx eas-cli init` in `apps/mobile`, and add `extra.eas.projectId` to `app.config.ts`.
3. First iOS build (`eas build -p ios --profile development`, later `production`): EAS registers `app.penciled` and `app.penciled.share-extension`, creates the App Group `group.app.penciled` and links it to both IDs. Let EAS manage credentials for **both** targets.
4. `eas submit -p ios --profile production` → TestFlight internal (creates the App Store Connect record if missing; then optionally put `ascAppId` in `eas.json`).
5. Play: create the app in Play Console, upload the **first AAB manually** to the internal track (the API cannot do the first upload), upload the service-account key to EAS, then `eas submit -p android --profile production`.
6. SP-3 run: 20 shares (Photos + screenshot thumbnail) on the iPhone; copy the `/share-spike` table into `docs/spikes/SP-3.md`. For release-like timing, set `EXPO_PUBLIC_SHARE_SPIKE=1` for a one-off build only, never for the store submission build.

### Open questions

- `aps-environment` is added to the iOS entitlements by `expo-notifications`; notifications are Android-only in the plan. If iOS needs no push, consider turning it off so the App ID needs no Push capability.
- expo-share-intent's `parseJson` calls `console.debug(e)` on a malformed iOS payload; the error text could contain fragments of the payload (file path/name). Library code, malformed input only; review before the real ingest (patch or wrapper).

## Open items

- Recursive **Casual** statics are not in `@expo-google-fonts/recursive`; make Casual 600 with fonttools in the theme sprint (UI.md §2.2).
- After `npx eas-cli init`, add `extra.eas.projectId` to `app.config.ts`.
- If ML Kit wrapper fails on a device build: fallbacks in `docs/spikes/SP-13.md` §4; escalate iOS failure to the Chair on day 2.

## Next

Builder runs SP-13 §7 (EAS login, dev builds, `/sp13` on both phones) and fills in §8, then the SPR-03 "Needs the builder" list above (enrolment, `eas init`, first iOS build, Play first upload, SP-3 20-share run on `/share-spike`).
