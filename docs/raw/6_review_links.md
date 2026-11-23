# Link verification (2026-11-19)

Method: WebFetch. Apple developer.apple.com doc pages are JS-rendered, so only the title came back (status "exists, body unverifiable"). Workaround found: append `.md` to Apple doc URLs (search surfaced `developer.apple.com/documentation/eventkit/accessing-the-event-store.md`); re-fetch Apple pages that way before relying on them.

Counts: ~43 URLs checked. OK (reachable and supports claim): 20. Problem (claim overstated, unsupported, or body unverifiable): 19. Skipped: 4 groups (below).

## Problems first

| URL | Claim in doc | Status / support | Fix |
|---|---|---|---|
| developer.apple.com/documentation/eventkit/accessing-the-event-store | P7: events write-only or full; reminders full only; write-only cannot read or delete own events; missing Info.plist keys = silent deny on iOS 17+ | Body blocked. Via search of the .md version: write-only "doesn't let it read any events... including events your app created"; "can't request read-only access". Delete by write-only NOT explicitly confirmed. "Silent deny" NOT confirmed | Use `.md` URL; soften "can't delete" to "can't fetch, so can't practically delete"; test missing-key behaviour on device |
| .../photos/phassetmediasubtype/photoscreenshot | P2 subtype | Exists (title only) | re-check via `.md` |
| .../photos/phphotolibrary | P2 limited access hides new screenshots | Title only; claim unconfirmed | `.md` |
| .../photos/phphotolibrarychangeobserver | change observer | Title only | `.md` |
| .../uikit/uiapplication/userdidtakescreenshotnotification | screenshot notification | Title only | `.md` |
| .../backgroundtasks/choosing-background-strategies-for-your-app | iOS background | Title only | `.md` |
| .../foundationmodels | P6 Apple-Intelligence-only | Title only; requirement unconfirmed | `.md` |
| .../devicecheck/establishing-your-app-s-integrity | SEC-ATTEST | Title only; exists | none |
| developer.apple.com/design/human-interface-guidelines/privacy | pre-explainers | Title only | `.md` |
| .../human-interface-guidelines/playing-haptics | "Apple advises against overuse" | Title only; claim unconfirmed | `.md` |
| support.google.com/googleplay/android-developer/answer/10787469 (Data safety) | P10: service-provider transfer is "collected", not "shared" | Page says transferring to a "service provider" is not sharing; does not call it "collected". Internal-testing exemption supported ("exclusively active on this track do not need to complete") | Reword: exempt from "sharing" disclosure but still counts as collection if data leaves the device |
| developer.apple.com/app-store/app-privacy-details/ | P10 App Privacy labels still required for TestFlight | Page says nothing about TestFlight/beta; uses "third-party partners" wording | Drop "for TestFlight" or find a source |
| developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview | "External TestFlight needs Beta App Review" | Overstated: "If you invite external testers, your beta build may require review." Needed for first build only | "First external build needs Beta App Review; later builds may not" |
| support.google.com/googleplay/android-developer/answer/14115180 | P5 READ_MEDIA_IMAGES restricted; declaration required | Partly: apps "may only request" it if system pickers insufficient. Declaration explicitly tied to custom pickers; does not say a background screenshot watcher qualifies as core use | Treat Play approval as a real risk; keep picker/share fallback |
| docs.expo.dev/build/introduction/ | EAS Build/Submit | Exists; submit only mentioned as integration | Add https://docs.expo.dev/submit/introduction/ (not fetched) |
| shopify.github.io/flash-list/docs/v2-changes | FlashList v2 + new architecture | Exists; page does not state a new-arch requirement | Verify in FlashList README |
| privacy.claude.com | SEC-RETAIN verified period | Landing page only, no period | Cite https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data (named in Anthropic docs, not fetched) |
| m3.material.io/styles/motion/easing-and-duration | `cubic-bezier(0.2, 0, 0, 1)` | Exists (title only); values unconfirmed | check page |
| developers.google.com/ml-kit/vision/text-recognition/v2 | P6 on device, line boxes, confidence | Boxes and confidence confirmed ("returns the bounding boxes, corner points, rotation information, confidence score"). "On device" not shown in fetched text | confirm on page |

## OK

| URL | Claim | Support |
|---|---|---|
| developer.android.com/reference/androidx/work/Constraints.Builder | P4 addContentUriTrigger API 24+ | `@RequiresApi(value = 24) addContentUriTrigger` |
| .../background-work/background-tasks/broadcasts | ACTION_NEW_PICTURE gone | "Android 7.0 (API level 24) and higher don't send" it |
| .../versions/14/features/partial-photo-video-access | Android 14 partial access | Selected Photos Access; READ_MEDIA_VISUAL_USER_SELECTED. Caveat: only when targeting API 34, else compat mode |
| .../identity/providers/calendar-provider | P8 intents need no permission | "your application doesn't need to request permissions". No-handle/no-Undo is design inference |
| .../provider/CalendarContract.Reminders | METHOD_ALERT, minutes | MINUTES and METHOD writable fields confirmed; METHOD_ALERT constant not seen (page truncated) |
| .../google/play/integrity | Play Integrity | Exists |
| .../custom-back/predictive-back-gesture | predictive back | Exists; default-on |
| developers.google.com/ml-kit/genai | P6 foreground-only | "inference is permitted only when the app is the top foreground application" |
| m3.material.io/components/snackbar | toast naming | Exists |
| docs.expo.dev/versions/latest/sdk/sharing/ | P3 experimental, opens main app | "experimental"; opens the main target; also "not officially supported by Apple" (add to risks) |
| docs.expo.dev/versions/latest/sdk/background-task/ | P4 vendor variance | "behavior varies by device vendor"; 15-minute minimum |
| docs.expo.dev/versions/latest/sdk/calendar/ | P8 | READ_CALENDAR/WRITE_CALENDAR; `writeOnlyAccess` option exists |
| docs.expo.dev/versions/latest/sdk/media-library/ | line 68 verify | RESOLVED: `MediaSubtype.SCREENSHOT` exists (iOS-only); limited access supported. The screen-dimension fallback can be dropped |
| docs.expo.dev/modules/overview/ | P11 | "write Swift and Kotlin" |
| docs.expo.dev/develop/development-builds/introduction/ | P11 | implied ("free to use any native libraries"); Expo Go not named |
| developer.apple.com/app-store/review/guidelines/ | P9 | 5.1.2(i) "including with third-party AI, and obtain explicit permission"; 5.1.1(iii) "use the out-of-process picker or a share sheet" |
| platform.claude.com/docs/en/about-claude/pricing | Haiku 5.5 $0.10/$0.50 to 100K | Confirmed. Over 100K: $0.50 in / $2.50 out. Cache hits $0.01/MTok (0.1x; resolves the "verify") |
| genai.owasp.org/llmrisk/llm01-prompt-injection/ | LLM01 | Exists |
| sqlite.org/fts5.html | FTS5 | Exists |
| w3.org/TR/WCAG21/#contrast-minimum | 4.5:1 / 3:1 | Confirmed |

## Anthropic retention (D3 / SP-6)
platform.claude.com/docs/en/manage-claude/api-and-data-retention: conversation content "is not retained by default; the exception is Covered Models, which require 30-day retention." Whether Haiku 5.5 is a Covered Model was not found on the page (search named Fable/Mythos 5.x). The design's "~30-day" assumption is conservative; cite this page in SP-6. Structured-output schema caching (24 h) came from search snippets only, unverified on the page.

## Skipped
- Anthropic structured-outputs docs (no URL in the design).
- Expo config plugins and Router formSheet docs (no URL in the design; add https://docs.expo.dev/router/advanced/modals/ and verify).
- iOS App Intents, Back Tap, Android MediaStore/WorkManager overview pages (mentioned in prose only).
- expo-share-intent community repo (marked verify, no URL; likely github.com/achorein/expo-share-intent, not fetched).
