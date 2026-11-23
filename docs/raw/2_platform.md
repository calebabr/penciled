# 2_platform.md — Platform research (design only)

Date: 2026-11-18. Labels: **[O]** = read on an official page this session; **[O-title]** = official URL cited but page text was not retrievable, claim from my prior knowledge; **[N]** = non-official (community, my judgment). Claims marked [N] or [O-title] must be confirmed in spikes.

## 1. Bottom line first
- **iOS cannot truly auto-detect a screenshot while the app is suspended.** Documented mechanisms need the app running (see 2). The honest iOS design is: share/import as the floor, plus catch-up scan on every app open, plus detection while the app is alive, plus an opt-in Shortcut/Back Tap path. Treat "notification a few seconds later with the app closed" as unproven on iOS until Spike 1.
- **Android can get closer** (WorkManager content-URI trigger on MediaStore), but needs broad photo permission, which Play policy restricts.
- Recommended v1: **Expo (React Native) development builds with 3 small custom native modules in Swift/Kotlin; iOS first, Android second.** Details in section 8.

## 2. iOS
**Photo access.** `PHPhotoLibrary.requestAuthorization(for:)` takes an access level (add-only or read/write), and status can be limited; `presentLimitedLibraryPicker` lets the user change the selection [O](https://developer.apple.com/documentation/photos/phphotolibrary.md). Apple's review guideline 5.1.1(iii) says use the out-of-process picker or share sheet instead of full Photos access where possible [O](https://developer.apple.com/app-store/review/guidelines/). Implication: with Limited access, new screenshots are not visible unless the user selects them. The app must detect `.limited`, say so, and offer share/import (matches F1(c)).

**Detecting new screenshots.**
- `PHAssetMediaSubtype.photoScreenshot` flags screenshot assets [O](https://developer.apple.com/documentation/photos/phassetmediasubtype/photoscreenshot.md); filter fetches with it.
- `PHPhotoLibraryChangeObserver` reports library changes made by any app [O](https://developer.apple.com/documentation/photos/phphotolibrarychangeobserver.md). The page says nothing about background delivery; I found no documented way to be launched by it [gap, Spike 1].
- `PHPhotoLibrary.fetchPersistentChanges(since:)` with a stored `PHPersistentChangeToken` returns what changed since the last run (iOS 16+) [O](https://developer.apple.com/documentation/photos/phphotolibrary.md). Use this for catch-up on launch and in background tasks; handle `persistentChangeTokenExpired` [O](https://developer.apple.com/documentation/photos/phphotolibrary/fetchpersistentchanges(since:).md). Also dedupe by `localIdentifier` (F1(d)).
- `UIApplication.userDidTakeScreenshotNotification` posts after a screenshot, with no `userInfo` and no image [O](https://developer.apple.com/documentation/uikit/uiapplication/userdidtakescreenshotnotification.md). It only helps while the app is running; the saved asset may appear a moment later, so pair it with a library fetch.

**Background execution.** Apple's strategy guide [O](https://developer.apple.com/documentation/backgroundtasks/choosing-background-strategies-for-your-app.md): `BGAppRefreshTask` gives up to 30 s at a time the system chooses; `BGProcessingTask` runs at low-activity times (often overnight, charging); a silent push (`content-available: 1`, priority 5) gives up to 30 s and is rate-limited past ~3/hour; `beginBackgroundTask` only extends foreground work. None is a "run on new screenshot" trigger. A silent push needs a server that knows a screenshot happened, which it does not. So background refresh is opportunistic: use it to catch up and pre-process, never as the promised experience. Expo's wrapper adds that tasks stop if the user force-quits, run only with battery/network, and need a physical device to test [O](https://docs.expo.dev/versions/latest/sdk/background-task/).

**Entry points.**
- Share extension: guaranteed path. Expo's own `expo-sharing` config plugin can add an iOS share extension with image activation rules, but marked **experimental**, and it opens the main app rather than processing in the extension, which Apple does not officially support [O](https://docs.expo.dev/versions/latest/sdk/sharing.md). Community alternative `expo-share-extension` [N](https://awesome.ecosyste.ms/projects/github.com%2Fmaxast%2Fexpo-share-extension).
- App Intents surface actions to Shortcuts, Siri, Spotlight, and the Action button [O](https://developer.apple.com/documentation/appintents.md). An intent taking an image input lets a user wire "Back Tap / Action button -> screenshot -> our intent" [N, my design inference; Spike 2]. This is the best "feels automatic" fallback on iOS.

**On-device OCR and models.**
- Vision `VNRecognizeTextRequest`: on-device, fast or accurate path, per-line confidence and bounding boxes, language list [O](https://developer.apple.com/documentation/vision/recognizing-text-in-images.md). Bounding boxes also serve the post-beta source highlighting.
- Foundation Models framework: on-device model on Apple Intelligence devices only; supports guided generation (`@Generable`), tool calling, and (new in the current docs) image prompts and Private Cloud Compute routing [O](https://developer.apple.com/documentation/foundationmodels.md). Apple Intelligence-only means ordinary phones cannot rely on it, which is the product's differentiator. OS version for the image and PCC features and the exact context limit: not stated in what I retrieved [Spike 3].
- Core ML embeddings for semantic search: [O-title](https://developer.apple.com/documentation/coreml); model choice and size are a spike (Spike 6).

**Calendar and reminders (EventKit).** [O](https://developer.apple.com/documentation/eventkit/accessing-the-event-store.md)
- Events: write-only access (`requestWriteOnlyAccessToEvents`) or full access; reminders: full access only. There is no read-only level.
- Write-only cannot read back anything, even events your app created, and lists a single virtual calendar. So **Undo of an event needs full access** (to fetch and delete by identifier), or EventKitUI. Decision for the actions council: Undo is an F4 acceptance criterion, so request full access, or only claim Undo while the in-memory `EKEvent` identifier is held [verify in Spike 4 that delete works with write-only].
- Info.plist keys: `NSCalendarsWriteOnlyAccessUsageDescription` or `NSCalendarsFullAccessUsageDescription`, plus `NSRemindersFullAccessUsageDescription`. Without them iOS 17+ silently denies the request.
- `EKEventEditViewController` runs out of process and needs no permission, a zero-permission fallback for the edit-then-confirm sheet.
- Expo's `expo-calendar` supports write-only and reminders, requires a development build, not Expo Go [O](https://docs.expo.dev/versions/latest/sdk/calendar/).

## 3. Android
**Photo access.** Android 14 adds Selected Photos Access with `READ_MEDIA_VISUAL_USER_SELECTED`; apps must handle partial grants and treat URI access as temporary [O](https://developer.android.com/about/versions/14/features/partial-photo-video-access). **Play policy** restricts `READ_MEDIA_IMAGES` to apps whose core purpose needs broad access; others must use the photo picker, and a declaration is required (compliance mandatory since 2025-05-28) [O](https://support.google.com/googleplay/android-developer/answer/14115180). Auto-detect of screenshots arguably is the core purpose, but acceptance is a reviewer judgment [risk; Spike 7].

**Detection.**
- `Activity.registerScreenCaptureCallback` (Android 14, `DETECT_SCREEN_CAPTURE` permission): per-activity, only while that activity is visible, no image, shows a system notice; ADB captures are not detected [O](https://developer.android.com/about/versions/14/features/screenshot-detection). Useful only in-app; not a solution for background.
- MediaStore + `ContentObserver` while the process lives, and **WorkManager `addContentUriTrigger`** to run work when a content URI changes (API 24+, with update/max delay settings) [O](https://developer.android.com/reference/androidx/work/Constraints.Builder). This is the realistic "new screenshot while app closed" path. Screenshots sit in a Pictures/Screenshots folder (`RELATIVE_PATH`) [N, varies by vendor; Spike 7]. Broadcasts such as `ACTION_NEW_PICTURE` were removed in Android 7 [O](https://developer.android.com/develop/background-work/background-tasks/broadcasts).
- Vendor battery killers can break WorkManager; Expo notes some vendors treat swipe-away as a kill [O](https://docs.expo.dev/versions/latest/sdk/background-task/).

**Entry points.** `ACTION_SEND` / `ACTION_SEND_MULTIPLE` intent filters (Expo config plugin handles these) [O](https://docs.expo.dev/versions/latest/sdk/sharing.md). Android share is simpler and more reliable than iOS.

**OCR and models.** ML Kit Text Recognition v2 (Latin, Chinese, Devanagari, Japanese, Korean; bounding boxes and confidence) [O](https://developers.google.com/ml-kit/vision/text-recognition/v2); on-device bundled model [O-title, confirm]. ML Kit GenAI on Gemini Nano via AICore: structured output, image description, embeddings with AppSearch, limited device list, **foreground-only** (background returns `BACKGROUND_USE_BLOCKED`), per-app quotas [O](https://developers.google.com/ml-kit/genai). So on-device LLM extraction on Android cannot run from a background worker; OCR runs there, LLM runs on the server.

**Calendar.** `CalendarContract` direct writes need `READ_CALENDAR`/`WRITE_CALENDAR`; the calendar intents (e.g. insert) need no permission but hand off to the Calendar app, where you cannot see if the user saved [O](https://developer.android.com/identity/providers/calendar-provider), [O](https://docs.expo.dev/versions/latest/sdk/calendar/). Direct writes are needed for confirm-in-our-sheet plus Undo. Android has no native reminders store; reminders = calendar event with a reminder, or a local notification [N]. Google Calendar REST API needs OAuth consent and (for sensitive scopes) Google verification [O-title](https://developers.google.com/calendar/api); avoid in beta.

## 4. Store review rules that bite
- Apple 5.1.2(i): must clearly disclose where personal data goes to third parties, **including third-party AI**, and get explicit permission first; purpose strings must be specific; 5.1.1(iii) data minimization [O](https://developer.apple.com/app-store/review/guidelines/). Design: a pre-permission screen naming the cloud LLM vendor and what is sent; per-user consent stored; decline path still offers manual share/import. TestFlight external testers go through Beta App Review [O-title](https://developer.apple.com/help/app-store-connect/test-a-beta-version/testflight-overview); App Privacy "nutrition labels" still need to be filled [O-title](https://developer.apple.com/app-store/app-privacy-details/).
- Google Play Data safety: "collect" = leaves device; processing by your own service provider is not "sharing"; apps only on internal testing tracks are exempt from the form, but not production [O](https://support.google.com/googleplay/android-developer/answer/10787469). Photos are a declared data type.

## 5. Framework comparison

| Need | Expo / React Native | Flutter | Native SwiftUI + Kotlin |
|---|---|---|---|
| Custom native code | Expo Modules API: Swift/Kotlin modules [O](https://docs.expo.dev/modules/overview/); dev builds, not Expo Go [O](https://docs.expo.dev/develop/development-builds/introduction/) | Platform channels / Pigeon, background isolates [O](https://docs.flutter.dev/platform-integration/platform-channels.md), [O](https://docs.flutter.dev/perf/isolates.md) | Native, no bridge |
| Share extension | `expo-sharing` plugin (experimental) or community plugin | Community plugins [N]; extension must be written natively | First-class (a separate target) |
| Background tasks | `expo-background-task` (BGTaskScheduler / WorkManager, JS runs via task-manager, 15 min min on Android) | Plugins or native code; Dart in background needs engine setup [O](https://docs.flutter.dev/packages-and-plugins/background-processes.html) | First-class; best control of `fetchPersistentChanges` |
| PhotoKit observer, Vision, EventKit | Own Swift module (Photos/Vision) + `expo-calendar` | Own Swift/Kotlin plugin | Direct |
| App Intents | Not covered by Expo docs I read; needs a native target (e.g. community `expo-apple-targets`) [N](https://www.mintlify.com/EvanBacon/expo-apple-targets) | Native target | First-class |
| 10,000-item feed | FlashList v2 (recycling; new architecture only; must memoize props) [N, library docs](https://shopify.github.io/flash-list/docs/v2-changes) | `ListView.builder` is lazy by design [O-title](https://docs.flutter.dev/perf) | `LazyVStack`/`UICollectionView` [O-title] |
| Premium native feel | Good with Reanimated/native gestures; native-feel effort is on you | Own renderer, consistent but not literally native controls | Best (system materials, sheets, haptics) |
| Claude Code reliability for a TS dev | High for JS/TS; moderate for native modules [N judgment] | Dart less familiar to builder; fewer references [N] | Swift is well-covered; two codebases for two platforms [N] |

Honest read: nothing in the hard list (observer, screenshot subtype, share extension, EventKit, Vision, App Intents) is cross-platform in any framework. All three require native Swift/Kotlin for those parts. The choice is therefore about the other 80%: the UI, state, networking, search UI, and LLM calls. That favors TS/React.

## 6. What Claude Code builds reliably (judgment [N], no official source)
Strong: TS/React screens, FastAPI, LLM calls, SQLite schemas, date-resolution tables. Moderate: small self-contained Swift/Kotlin modules with a clear spec. Weak: Xcode project/entitlement/signing wrangling, share-extension target setup, TestFlight/Play first-time setup, anything only reproducible on a physical device (background behavior). Mitigation: config plugins and `expo-apple-targets` generate targets from code; keep native modules under ~200 lines each; test on real devices from week 1.

## 7. Risks to flag to the Round 3/4 council
1. F1(b) "auto-detect notification" is not honestly promised on iOS; rewrite acceptance as "within N seconds of opening the app, or immediately via Shortcut/Back Tap/share".
2. Limited Photos access silently hides screenshots: UI must show access state.
3. Undo vs write-only calendar access conflict (section 2).
4. Android broad photo permission may fail Play review in production; internal testing is lower risk.
5. Foundation Models and Gemini Nano cannot be the pipeline's core (device-gated, foreground-only on Android); cloud LLM is the core, consistent with FEATURES.md.

## 8. Recommended v1 platform
**Expo SDK (React Native, new architecture) with development builds; TypeScript UI; three local Expo modules.**
- iOS module: PhotoKit (limited-access state, screenshot-subtype query, persistent-change catch-up, observer while alive) + Vision OCR (+ optional embeddings).
- Android module: MediaStore query + WorkManager content-URI trigger + ML Kit OCR.
- Calendar: `expo-calendar` (full access on iOS, `WRITE_CALENDAR` on Android).
- Share: `expo-sharing` plugin first; fall back to a community plugin or a small hand-written Swift share target if Spike 2 fails.
- List: FlashList v2 with fixed-size thumbnail rows; thumbnails from the OS (PHImageManager / MediaStore) not full images.
- Ship **iOS to TestFlight first** (testers' phones are likely iPhones; Apple's sharper permission model makes it the harder test). Android internal testing second, with share + foreground scan guaranteed and WorkManager trigger as target.
- Why not SwiftUI-only: builder is strong in TS/React/Python, Android testers are lost, two codebases. Why not Flutter: adds Dart with no gain on the native-only hard parts. Fallback trigger: if the share extension or PhotoKit module cannot be made reliable by end of Spike 2, switch iOS to SwiftUI + keep RN only if Android justifies it.

## 9. Spikes the build must run (physical devices, week 1-2)
1. **iOS background detection:** does anything launch or wake the app on a new screenshot while suspended (observer, `BGAppRefresh`, `userDidTakeScreenshot`)? Measure latency from screenshot to catch-up on foreground, and how often BG refresh fires over 3 days.
2. **iOS share extension + Shortcut/Back Tap:** image arrives in app within 2 s (F1(a)); expo-sharing experimental path survives a TestFlight build; App Intent with image input works from Back Tap.
3. **Foundation Models availability and limits:** minimum OS, device list, image-prompt support, context size, whether usable from a background task. Decide whether it is used at all.
4. **EventKit:** write-only vs full: can we delete what we created (Undo)? Reminders full access prompt wording and denial recovery.
5. **Limited Photos:** behavior of `fetchPersistentChanges` and the observer under `.limited`; picker UX.
6. **Embeddings and search:** on-device model size, per-item cost, p95 query time at 10,000 items; FlashList scroll at 10,000 thumbnails on an older iPhone and a mid Android.
7. **Android:** does WorkManager content-URI trigger fire on screenshots on Pixel and Samsung; screenshot folder path; Play permission declaration wording; behavior with partial access.
8. **Review readiness:** Beta App Review passes with AI-disclosure screen; Data safety/App Privacy answers drafted; purpose strings reviewed.
9. **Expo specifics:** `expo-sharing` and `expo-background-task` are marked experimental or new in the docs; confirm SDK version compatibility and that Expo Updates does not crash extensions (community plugin note) [N].
