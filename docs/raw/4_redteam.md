# 4 — Red team (Round 4, design only)

Context: about 6 working weeks to mid-January, a solo non-native developer, Claude Code session caps, and a **Windows dev machine** (this session's environment). Sev = damage, Lik = likelihood.

## A. Attacks

**R1. iOS native work from Windows. Critical / High.** Swift modules and extension targets can't be built or debugged without a Mac; every attempt is an EAS cloud build plus a device install, on a capped free tier. Platform §6 rates this "weak" for Claude Code. **Cut:** without Mac access in week 1, the iOS beta is the main app plus a config-plugin share extension, using RN ML Kit OCR (arch §1) and `expo-media-library` for catch-up (verify it exposes the screenshot subtype). No custom Swift.

**R2. "Automatic" works only on Android, and testers have iPhones. Critical / High.** Platform §8 expects iPhone testers, and iOS can't notify on a new screenshot (platform §1). On iOS the flow is screenshot, thumbnail, share, pick app. **Cut:** a separate magic moment for each platform. On iOS it is share-to-card in 2 s or less, measured that way. Drop Back Tap and the App Intent.

**R3. Kotlin trigger, TypeScript pipeline. Critical / High.** The pipeline, validator and API client are TS (arch §9). The WorkManager trigger fires while the app is closed, so OCR → guard → redact → HTTP → validate → notify has to run headless. No document designs this. **Alternative:** spike headless JS in week 1. If it fails, use a thin Kotlin path: ML Kit, then guard/redact from a shared JSON regex ruleset, then POST. The server grounds, resolves and validates (AI §0) and returns the notification text. This also settles C5: one AI-RESOLVE, in Python.

**R4. The magic moment is unreliable on real screenshots. High / High.**
- Flyers have stylised text over images, the weak case for OCR-first (AI §1). With images off by default (D2), the hero example ends as a silent "Not sure" card.
- Chats: OCR loses sender and order. Negotiations ("Sat?" / "no, Sun") pick the wrong day. "tmrw" is anchored to capture time, not to when the message was sent (AI §5).
- Flyers rarely print a year, so a blocking "Year assumed" flag appears on most cards.

**Alternatives:**
- (a) Send images by default for share/import, which the user starts, and make it opt-in for auto-detect.
- (b) Anchor chat dates to OCR'd day headers ("Yesterday", "Mon 3:12 PM"), otherwise flag them.
- (c) A year inferred by the grace rule is shown, not blocking.
- (d) Week 1: run 50 real flyers and chats, text-only vs. image, before any UI.

**R5. Permission wall. High / High.**
- iOS asks for Photos (full), Notifications, Calendar *full* (scary wording) and Reminders.
- Android asks for READ_MEDIA_IMAGES (limited is offered on 14+), POST_NOTIFICATIONS, Calendar and exact alarms (actions §2).
- UI ONB-4 asks for notifications only after the first proposal. On Android the first proposal *is* a notification, so it fails silently on Android 13+.

**Cut:** a deadline or ladder becomes **one calendar event with up to 3 alarms** (`EKAlarm`, `CalendarContract.Reminders`). That removes the Reminders permission, ACT-REM, AlarmManager, BOOT_COMPLETED and the local-notification fallback, and gives one item with one undo. On Android, ask for notifications right after Photos.

**R6. UI scope. High / High.** Nine screens, Style Dictionary (TS + Swift), Storybook, pixel diffs, a content extension, fly-ins, morphs, AX5 reflow: not finishable beautifully. **Cut to 4 screens:** Onboarding (3 pages), Home (Ready cards + library + search field), Confirm sheet, and Settings/Privacy with History. One `theme.ts`. **Keep:** draft vs. confirmed styling, flags, the undo toast, dark mode, error and empty states, and a 200% text smoke test.

**R7. Expo dependency matrix. High / Medium.** Risky combinations: the experimental `expo-sharing` extension; sqlite-vec plus SQLCipher plus a `vec0` TEXT key (privacy §2, scalability §2); `onnxruntime-react-native` on the new architecture; FlashList v2. **Cut:** FTS5-only search (arch D5 allows it), no SQLCipher (rely on the OS sandbox and disclose it), and pin the Expo SDK in week 1.

**R8. Server over-engineered for ~50 testers. Medium / High.** JWT refresh, attestation, 7 tables, remote config, queue flag, OTel. **Alternative:** one stateless endpoint, invite-code token, daily counter, provider spend cap as kill switch. Keep two fixes: an idempotency key that stays the same across retries, and a retry budget of 3 (scalability §3).

**R9. Cost blows up only by accident. Medium / Medium.**
- The first catch-up treats the whole library as new.
- Up to 18 provider calls per item when retries stack (scalability §3).
- Sonnet escalation is 45% of spend (AI §13).

**Cut:** an install-time watermark, no Sonnet in the beta, and a $25/month provider cap. Even 10× AI §13's estimate is a few dollars a month for 50 testers.

**R10. Privacy. High / Medium.**
- "Nothing is saved on the server" and "zero-retention" overclaim: ZDR may not be available to a solo developer (privacy §6, D3).
- Chat text includes third parties' names, and redaction doesn't remove them.
- The guard only understands English.
- "Send anyway" breaks F7(b).
- Android source-app detection needs usage access.

**Cut:** onboarding copy states the real retention period and that names are sent. Drop "Send anyway" and source-app detection.

**R11. Store gates over the holidays. High / Medium.**
- Apple: external TestFlight needs Beta App Review, a privacy policy URL and an explicit 5.1.2(i) AI-consent tap, and review slows in late December.
- Play: identity verification, the READ_MEDIA_IMAGES declaration (D8), and USE_EXACT_ALARM (restricted to alarm/calendar apps).

**Cut:** enrol in both stores and push a hello-world build through TestFlight and Play internal testing in week 1. Use internal tracks (100 testers or fewer).

**R12. Eval effort. Medium / High.** 520 hand-labelled images, a blind second labeller, 3-run bootstrap CIs and 7 snapshot suites. **Cut:** 150 images (100 synthetic, 50 own) and single runs. Hard gates are the date suite and no network for sensitive images. Everything else is report-only.

**R13. Backlog and 10k creep. Medium / High.** Backlog import is post-beta (FEATURES queue #4), yet AI §11 and scalability B1 build its foundation now. **Cut:** no bulk import; multi-select capped at 20; 10k-scroll tested on seeded data; DB excluded from OS backup (avoids the 25 MB cap).

**R14. Anchor and timezone. Medium / Medium.** The "tz at capture" (arch §4) can't be known for imported or forwarded images. **Alternative:** show the anchor ("relative to Tue Nov 18"), changeable with one tap.

## B. Internal contradictions

| # | Conflict | Files |
|---|---|---|
| C1 | Two vs three native modules; plus a content extension and an App Intent target | arch §1 vs chair D6, platform §8; UI §7, platform §5 |
| C2 | iOS first vs Android first | platform §1/§8 vs chair D6, arch §1 |
| C3 | OCR: RN ML Kit on both vs Vision in Swift | arch §1 vs platform §8, AI §1 |
| C4 | JobScheduler vs WorkManager | arch §1 vs platform §3 |
| C5 | Validate/resolve on device (TS) vs server (Python) | arch §2/§3 vs AI §0/§5, eval §4 |
| C6 | Schema: numeric conf, `start_text`/`src`, 3 classes vs labels, `RawWhen`, 5 classes | arch §8 vs AI §4 |
| C7 | All flags block vs `assumed` doesn't block; AM/PM blocks vs AM/PM is an assumption | UI SCR-CONFIRM vs AI §6; actions §1 vs AI §5 |
| C8 | Image policy (global opt-in / auto for share / per item); size 1024/1568/1280 px | chair D2, AI §1, privacy SEC-MIN-IMAGE; arch §2 |
| C9 | Chats not sensitive vs message UI = sensitive | chair D1 vs privacy §3, eval §1 |
| C10 | "Send anyway" vs never sent | privacy SEC-GUARD-BIAS vs FEATURES F7(b) |
| C11 | Write-only calendar vs full access | UI ONB-4 vs chair D7, actions §1 |
| C12 | "Nothing saved"/zero-retention vs unverified | UI ONB-2, arch §3 vs privacy §6, D3 |
| C13 | DB backed up vs excluded | arch §5 vs privacy SEC-REST-DEVICE |
| C14 | float32 + RRF vs int8 + linear | arch §4 vs AI §8 |
| C15 | Token 15 min vs 1 h; caps 200/day vs 300/day vs none | arch §7 vs privacy §4 vs AI §11 |
| C16 | Time-to-card 6/15 vs 2.5/5 vs 5/10 s | arch §9 vs AI §12 vs eval QA-PERF-03 |
| C17 | Undo toast 6 vs 10 vs ≥8 s | UI CMP-TOAST vs actions §1 vs eval QA-A11Y-06 |
| C18 | Day-before rung at 09:00 vs 18:00 | AI §5 vs actions §3 |
| C19 | Meaning search needs network vs on-device | UI SCR-SEARCH vs arch §2, AI §8 |
| C20 | Deleting server copies vs none stored | UI SCR-DETAIL, privacy SEC-DEL-ONE vs arch §6 |
| C21 | Notification prompt deferred vs Android proposal is a notification | UI ONB-4 vs FEATURES F1(b) |
| C22 | Reminders fire in 60 s (19/20) vs p95 under 2 min | eval BAR-08 vs actions §3 |
| C23 | Backlog post-beta vs built now; 3 vs 20 shots/day | FEATURES queue #4 vs AI §11, scalability B1; arch §10 vs scalability §0 |
| C24 | Idempotency key changes on retry | arch §8 (scalability §3) |

## C. Forced cuts (ranked)

1. iOS = share extension + catch-up on open only (R1, R2).
2. Week-1 spikes before UI: headless JS; text vs image on real screenshots (R3, R4).
3. Reminders/ladder become calendar alarms (R5).
4. UI = 4 screens (R6).
5. FTS5-only search, no SQLCipher (R7).
6. One-endpoint server (R8).
7. No backlog import; install-time watermark (R9, R13).
8. 150-image eval (R12).
9. No "Send anyway", source-app detection or Sonnet; honest retention copy (R9, R10).
10. Store enrolment and hello-world builds in week 1 (R11).
