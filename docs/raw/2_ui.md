# 2_ui.md: UI/UX design (Round 2, design only)

Scope: the locked beta (F1–F8) only. Principle, made visible: **the model proposes (draft styling), code validates (flags), the user confirms (one solid tap).** All screens are written so they map onto SwiftUI or React Native/Expo. Platform-specific notes are marked **[iOS]**, **[Android]** or **[RN]**.

## 1. Design principles + visual direction

1. **Draft until you tap.** Proposed items look like drafts: a dashed or tinted outline, "Proposed" label, editable fields. Only after confirm do they become solid with a check. This puts the core principle into the visuals: users can always tell what has happened and what has only been suggested. (Apple's own screenshot actions also output a draft the user verifies; see FEATURES F2.)
2. **Show the doubt.** Uncertain or assumed fields get one amber highlight plus a reason ("Year assumed: 2027"). Doubt is never hidden and never shown everywhere. One clear flag beats five weak ones.
3. **The screenshot is the hero.** Every proposal sits next to its source thumbnail, so checking a field means glancing left. The chrome stays quiet: neutral surfaces, one accent.
4. **Fast and calm.** The card should appear within seconds. Motion confirms what happened and is never decorative. Every action has an undo within reach.
5. **Honest by default.** Data flow is shown before any permission ask, and sensitive screenshots get a visible "Kept on device" badge.

**Visual direction: "quiet paper + one ink."** Off-white/near-black canvases, a single indigo accent for actions, amber reserved only for "check this," and generous type in the spirit of Things 3, which reviewers praise for a light background, generous typography and fluid animation ([LifeStack review](https://lifestack.ai/blog/things-3-review)). Field "fly-in" feedback borrows from Fantastical, where parsed words highlight and fly into the event form ([MacStories](https://www.macstories.net/reviews/the-new-fantastical-review/), [Daring Fireball](https://daringfireball.net/linked/2025/06/03/event-creation-still-largely-feels-like-an-unsolved-ui-problem)). Why: the product's whole risk is trust, so the UI must look precise and restrained, not "AI-sparkly." No gradients, no sparkle icons, no chat bubbles.

## 2. Design system

### 2.1 Color tokens (semantic; hex)
| Token | Light | Dark | Use |
|---|---|---|---|
| `bg.canvas` | #F7F7F5 | #0B0B0D | screen background |
| `bg.surface` | #FFFFFF | #17171A | cards, sheets |
| `bg.elevated` | #FFFFFF | #212126 | sheets over sheets, toasts (dark) |
| `bg.sunken` | #EFEFEC | #111114 | search field, chips idle |
| `text.primary` | #111113 | #F2F2F4 | body, titles |
| `text.secondary` | #5E5E66 | #A1A1AA | metadata (≥4.5:1 on surface) |
| `text.tertiary` | #8A8A93 | #71717A | placeholders only (non-essential) |
| `border.hairline` | #E4E4E0 | #2A2A30 | dividers |
| `accent` | #4F46E5 | #8B87FF | primary buttons, links, selected |
| `accent.onAccent` | #FFFFFF | #0B0B0D | text on accent |
| `accent.tint` | #EEF0FF | #22214A | draft card fill, chip selected |
| `flag` | #B45309 | #FBBF24 | uncertain-field text/icon |
| `flag.tint` | #FEF3C7 | #3A2A08 | uncertain-field fill |
| `success` | #15803D | #4ADE80 | confirmed state |
| `danger` | #C62828 | #F87171 | errors, delete |
| `private` | #0F766E | #2DD4BF | "Kept on device" badge |

Rule: never encode state by color alone. Flags carry an icon plus a text reason, and confirmed items carry a check.

### 2.2 Typography
Use the system font (SF Pro on [iOS]; Roboto/Google Sans-style system on [Android]; in RN, leave `fontFamily` unset so it inherits). Sizes are scaled by Dynamic Type / font scale.

| Token | Size/Line | Weight | iOS text style |
|---|---|---|---|
| `type.display` | 34/41 | Bold | largeTitle |
| `type.title` | 22/28 | Semibold | title2 |
| `type.headline` | 17/22 | Semibold | headline |
| `type.body` | 17/22 | Regular | body |
| `type.callout` | 16/21 | Regular | callout |
| `type.footnote` | 13/18 | Regular | footnote |
| `type.caption` | 12/16 | Medium | caption1 |
| `type.mono` | 15/20 | Regular, tabular nums | (dates/times in fields) |

### 2.3 Spacing, radii, elevation, icons
- **Spacing (4-pt):** `space.1`=4, `2`=8, `3`=12, `4`=16 (screen gutter), `5`=20, `6`=24, `8`=32, `10`=40.
- **Radii:** `radius.sm`=8 (chips, fields), `radius.md`=14 (thumbnails), `radius.lg`=20 (cards), `radius.xl`=28 (sheet top corners), `radius.full` (pills). Use continuous corners on [iOS] (`.continuous`); RN approximates them with plain radii.
- **Elevation:** few shadows. `elev.0` flat with hairline border (list rows); `elev.1` card: y2 blur8 #000 6% (light), and in dark a lighter surface instead of a shadow; `elev.2` sheet/toast: y8 blur24 #000 12%.
- **Icons:** SF Symbols on [iOS] (`calendar.badge.plus`, `bell`, `exclamationmark.triangle`, `lock.shield`, `arrow.uturn.backward`); Material Symbols Rounded on [Android]/RN (`expo-symbols` on iOS, `@expo/vector-icons` MaterialSymbols elsewhere). Glyphs are 20 pt inline and 24 pt in nav, regular weight. Icons get a text label wherever an action matters.

### 2.4 Component library
| ID | Component | Spec |
|---|---|---|
| CMP-THUMB | Screenshot thumbnail | 9:19.5 crop, `radius.md`, hairline border; long-press opens a preview |
| CMP-ACTIONCARD | Action-ready card | thumbnail left (64×138), right: class label ("Event · Proposed"), title (`headline`), 2–3 field rows, flag count pill, buttons [Review] [Add] (Add disabled while flags are open). Draft style: `accent.tint` fill + 1pt dashed `accent` border; confirmed: solid surface + green check |
| CMP-FIELDROW | Editable field row | label (caption, secondary) / value (body or mono). Flagged variant: `flag.tint` fill, ⚠ icon, reason line ("Year assumed"). Tap opens the native picker inline |
| CMP-CHIP | Action chip | pill, 32 pt tall (44 pt hit area), icon + label; states idle/selected/disabled. Used for deadline-ladder presets ("Day before ✓", "Morning of ✓", "2 h before"). |
| CMP-SHEET | Bottom sheet | detents medium/large, grabber, `radius.xl`. [iOS] `.sheet` + `presentationDetents`; [RN] `@gorhom/bottom-sheet`; [Android] M3 ModalBottomSheet |
| CMP-BTN | Buttons | Primary: filled accent, 50 pt, `radius.full`, full width in sheets. Secondary: tinted. Tertiary: text. Destructive: danger text. Pressed state: scale 0.97 + 8% darken |
| CMP-ROW | List row | 56–72 pt, leading icon/thumb, title/subtitle, trailing value or chevron; swipe actions (Undo, Delete) |
| CMP-SEARCH | Search bar | `bg.sunken` field, magnifier, placeholder "Search by what you remember"; scope chips below (All · Events · Deadlines · Nothing to do) |
| CMP-TOAST | Toast/snackbar | bottom, above the tab bar, `bg.elevated` (inverted in light: #1C1C1F with white text), message + [Undo]; 6 s, paused while touched or while VoiceOver focus is on it |
| CMP-BANNER | Inline banner | full-width, icon + text + action; variants info/warn/error/offline/private |
| CMP-BADGE | Status badge | small pill: Proposed / Added / Undone / Kept on device / Nothing to do |
| CMP-SKELETON | Skeleton | shimmer-free pulse (opacity 0.5↔1, 1.2 s); static under reduced motion |
| CMP-EMPTY | Empty state | 96 pt line illustration (single-stroke, accent), title, one sentence, one button |

## 3. Motion and haptics

Durations follow a Material-3-like scale (short 100–200 ms, medium 250–350 ms, long 400–500 ms; standard curve `cubic-bezier(0.2,0,0,1)`, emphasized decelerate for entrances). Verify against [M3 easing & duration](https://m3.material.io/styles/motion/easing-and-duration). On [iOS], prefer springs (`.spring(response:0.35, dampingFraction:0.85)`). In [RN], use Reanimated `withSpring({damping:18, stiffness:220})`.

| Moment | Motion | Haptic |
|---|---|---|
| Card arrives in feed | slide down 12 pt + fade, 300 ms; siblings shift with layout animation | none (avoid noise) |
| Field "fly-in" while extracting | each field value fades/slides from the thumbnail side, staggered 60 ms | none |
| Flag appears | amber fill wipes in, 200 ms; no shake | none |
| Fix a flagged field | amber fades to neutral, ⚠ morphs to ✓, 250 ms | selection tick |
| **Confirm (Add)** | button morphs into a check circle (200 ms), the draft's dashed border goes solid while the tint drains to surface (300 ms), the card compresses to a compact "Added" row (350 ms), and the toast rises | `notification.success` |
| Undo | reverse morph back to draft; toast swaps to "Removed from Calendar" | `impact.light` |
| Error | banner slides in; button returns to idle | `notification.error` |
| Sheet | system sheet spring | system |
| Processing | indeterminate progress plus three named steps (Reading → Understanding → Checking dates); a step ticks when done | none |

Rules: motion ≤ 500 ms; nothing loops except processing; haptics only for confirm/undo/error/selection, following Apple's caution against overuse ([HIG Playing haptics](https://developer.apple.com/design/human-interface-guidelines/playing-haptics)). [RN]: `expo-haptics` maps `notificationAsync(Success)` and `selectionAsync`. On [Android], this degrades to `performHapticFeedback(CONFIRM)`.

## 4. Screens and states

### SCR-ONBOARD (onboarding + permissions)
Goal: get the most permission acceptance by showing value and data flow *before* each system prompt, and asking in context. Both Apple HIG pages say to avoid launch-time asks unless the permission is needed, and to add a custom explainer before the system alert ([HIG Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy), [HIG Onboarding](https://developer.apple.com/design/human-interface-guidelines/onboarding)).

Flow (4 pages max, skippable after page 2):
1. **ONB-1 Value:** looping 3-second demo (reduced-motion: still frame) of a flyer screenshot turning into a card. "Screenshots that turn into plans."
2. **ONB-2 Data flow (F7a):** a plain-language diagram (Phone → "Text from the screenshot is sent to our server to understand it" → "Nothing is saved on the server after processing*" → Your calendar). Sensitive screens stay on device. [Learn more] links to SCR-PRIVACY. *Exact copy depends on what the architecture decision says; never overclaim.
3. **ONB-3 Try it:** a bundled sample flyer → the user taps it → the real magic moment runs on sample data. Value is proven before any permission ask.
4. **ONB-4 Permissions, one at a time, each with pre-explainer card:**
   - Photos (for auto-detect, F1): "Let us notice new screenshots." [Allow access] → system prompt. **[iOS]** limited library access is likely, so explain that "Selected photos" means we can't see new screenshots; offer share-sheet instead.
   - Notifications: asked *after* the first real proposal ("Want a heads-up next time?"), not here.
   - Calendar/Reminders: asked at first [Add] tap (point of use). **[iOS 17+]** write-only calendar access is enough to request; it's less scary.

```
┌──────────────────────────┐
│        ( ● ● ○ ○ )        │
│   Phone ──▶ ☁ Understand  │
│     │        (not stored) │
│     ▼                     │
│  🔒 Banking, IDs, health  │
│     stay on this phone    │
│                           │
│ You approve every action. │
│ Nothing is added without  │
│ your tap.                 │
│ [ Continue ]  Learn more  │
└──────────────────────────┘
```
States: permission denied → CMP-BANNER on home "Auto-detect is off. Share screenshots to the app instead. [How] [Settings]" (F1c; never fail silently).

### SCR-HOME (home feed)
Layout: large title "Screenshots"; a top "Ready" section with horizontally paged CMP-ACTIONCARDs (or stacked, max 3, then "See all"); below, a "Library" grid of CMP-THUMBs (3 columns, virtualized: [iOS] `LazyVGrid`, [RN] FlashList, to meet the 10k-item scroll bar), each with a CMP-BADGE overlay. Tab bar: Home · Search · History; Settings sits behind the avatar/gear on Home. FAB-less: the import button is a "+" in the nav bar (opens the photo picker / Files).
```
┌──────────────────────────┐
│ Screenshots       +   ⚙  │
│ READY (2)                 │
│ ┌──────────────────────┐ │
│ │▯ Event · Proposed     │ │
│ │▯ Pizza Night          │ │
│ │▯ Fri Jan 22 · 7:00 PM │ │
│ │▯ ⚠ 1 to check         │ │
│ │  [Review]   [ Add ]   │ │
│ └──────────────────────┘ │
│ LIBRARY                   │
│ ▯ ▯ ▯   ▯ ▯ ▯   ▯ ▯ ▯     │
│ Home   Search   History   │
└──────────────────────────┘
```
States:
- **Empty (new user):** CMP-EMPTY "Take a screenshot of a flyer or plan. It'll show up here." [Import a screenshot].
- **Loading (cold launch):** skeleton grid, 6 tiles; the Ready section is hidden until loaded.
- **Processing item:** thumbnail with a pulsing ring + "Reading…" badge; tap opens SCR-DETAIL with step progress.
- **Nothing to do:** the item lands silently in the Library with a grey "Nothing to do" badge; no card, no notification (F2d).
- **Offline:** CMP-BANNER offline "You're offline. New screenshots will be read when you reconnect." Queued items show "Waiting" badges.
- **Error per item:** badge "Couldn't read" with [Retry] on the detail page.

### CMP-ACTIONCARD (action-ready card) in detail
Shows up to 3 actions from one screenshot (F2e) as stacked sub-rows inside one card: "Event: Pizza Night" + "Reminder: RSVP by Wed". Each has its own checkbox (default on). The primary button reads "Add 2". Assumptions show inline (F3): "Fri → Jan 22 (from screenshot date)". The same card appears in the notification's rich expansion **[iOS]** (Notification Content Extension; Android uses BigPicture + action buttons). The notification [Add] button is offered only when there are 0 flags; otherwise it shows only [Review].

### SCR-CONFIRM (edit-before-confirm sheet)
CMP-SHEET at large detent. The top half shows the screenshot, zoomable and pinch-able; the bottom half shows fields. When the sheet opens, focus goes to the first flagged field.
```
┌──────────────────────────┐
│ ▔▔▔                       │
│ [  screenshot preview   ] │
│ ───────────────────────── │
│ Event          Proposed   │
│ Title   Pizza Night       │
│ Starts  Fri Jan 22 7:00PM │
│░⚠ Year  2027  "assumed:  ░│
│░  no year on flyer" [Fix]░│
│ Ends    —  (not found)    │
│ Where   Student Center    │
│ Calendar  Personal ▾      │
│ ───────────────────────── │
│ ☑ Reminder: RSVP by Wed   │
│   Ladder: [Day before✓]   │
│   [Morning of✓] [2h ▢]    │
│ [  Add event + reminder ] │
│   Discard proposal        │
└──────────────────────────┘
```
- Missing fields show "— not found" (F2c) and are never filled with placeholders that look like data.
- The primary button stays disabled until every flag is resolved (confirmed as is, or edited). A flag can be accepted with "Looks right" so users aren't forced to edit.
- Deadline ladder (F5): CMP-CHIPs; any chip that would fall in the past is disabled with the caption "Already passed."
- Error states: calendar permission denied → inline banner + [Open Settings]; the proposal is kept (F4d). Write failure → "Couldn't add to Calendar. Your edits are saved." [Try again].
- Discard → card disappears with undo toast "Proposal dismissed" (no side effects, F4e).

### SCR-SEARCH
CMP-SEARCH autofocused, scope chips, recent searches. Results: CMP-ROW with thumb, matched snippet with the query term bolded, and the class badge. Semantic matches get a subtle "Related" label so users understand why a non-literal hit appeared.
States: **empty query**: recent searches + "Try 'pizza flyer' or 'dentist'"; **no results**: "Nothing matched. Try fewer words."; **loading**: inline spinner in the field after 150 ms (no flash for fast results); **offline**: text search still works, with the caption "Meaning search needs a connection" (if embeddings are server-side; platform-dependent).

### SCR-DETAIL (screenshot detail)
Full-bleed screenshot (pinch zoom), then a pull-up panel: class badge, extracted fields (read-only unless the proposal is still pending), an action history timeline ("Added to Calendar · Jan 10, 9:41 · [Undo]"), the extracted text (collapsible, selectable), and a privacy line ("Processed on server · not stored" or "Kept on device"). Overflow: Re-run, Delete this screenshot's data (confirm dialog explains what is removed, incl. server copies, F7d).
Processing state: three-step progress (Reading → Understanding → Checking dates). Error: "Couldn't read this image." [Retry] [Report].

### SCR-HISTORY (history/undo)
Reverse-chronological CMP-ROWs grouped by day: icon (calendar/bell), "Added 'Pizza Night' to Personal", source thumbnail, trailing [Undo] (becomes "Undone" badge). Undo always asks for confirmation if the event was edited in the calendar app afterwards (code detects this). Empty: "Nothing added yet. Actions you approve show up here, and you can undo them."

### SCR-SETTINGS + SCR-PRIVACY
Grouped list ([iOS] `Form`/inset grouped; [Android] M3 list):
- Capture: Auto-detect status (on / limited / off, with a fix link), Notifications.
- Defaults: calendar, reminder list, default ladder presets, time zone shown.
- **SCR-PRIVACY:** the data-flow diagram from ONB-2, "What leaves this phone" list, sensitive-content guard toggle (on by default, explained), beta analytics ("Counts only, never content", toggle, F8), Delete all my data (destructive, two-step: type-free confirm dialog + final result screen "Deleted from phone and server").
- About, Send feedback, Component Gallery (debug builds only, see §7).

### Global states (SCR-STATES)
| ID | State | Treatment |
|---|---|---|
| ST-OFFLINE | no network | banner + queued badges; never lose an import |
| ST-PERM-LIMITED | limited photos | banner explaining share-sheet path |
| ST-SENSITIVE | sensitive detected | teal "Kept on device" badge; no cloud proposal; detail explains why |
| ST-SERVER-ERR | API failure | per-item "Couldn't read · Retry"; auto-retry with backoff, silent unless 3 failures |
| ST-SLOW | >8 s processing | step text changes to "Taking longer than usual…" |

## 5. The magic moment, frame by frame

| # | Time | Frame |
|---|---|---|
| F0 | 0 s | User screenshots a club flyer in Instagram. Nothing interrupts them. |
| F1 | ~3–6 s | Notification: "**Ready to add:** Pizza Night · Fri Jan 22, 7 PM + RSVP reminder. 1 thing to check." Thumbnail attached. |
| F2 | tap | App opens straight into SCR-CONFIRM over Home (deep link). Fields fly in from the screenshot side, staggered (Fantastical-style). |
| F3 | +0.5 s | One amber row pulses once: "Year assumed: 2027". Focus lands there. |
| F4 | user | Taps "Looks right". Amber → neutral, ⚠ → ✓, selection haptic. The button activates: "Add event + reminder". |
| F5 | tap | Button morphs to a check, success haptic, sheet dismisses, card goes solid and compacts to "Added ✓". |
| F6 | +0.3 s | Toast: "Added to Calendar · 2 reminders set  [Undo]" (6 s). |
| F7 | later | History shows the entry with Undo; the calendar event shows the source note "From screenshot · Snap app". |

Target: tap-to-done ≤ 2 taps when there are no flags, and ≤ 3 with one flag.

## 6. Accessibility
- **Dynamic Type / font scale:** all text uses tokens tied to text styles and supports up to AX5 (iOS) / 200% (Android). At accessibility sizes, CMP-ACTIONCARD reflows to a vertical layout (thumb on top) and field rows stack label over value. In RN, cap scaling per element only for the tab bar (`maxFontSizeMultiplier=1.5`).
- **Contrast:** text pairs in §2.1 meet WCAG AA 4.5:1 (secondary on surface ≈ 6:1; flag #B45309 on #FEF3C7 ≈ 4.6:1, to verify with a checker in the token test); non-text UI ≥ 3:1. Support Increase Contrast with a high-contrast token set (border.hairline → text.secondary; dashed draft border 2 pt).
- **Screen readers:** each card is one element with a combined label: "Proposed event, Pizza Night, Friday January 22, 7 PM, Student Center. 1 field needs checking." Actions are exposed as custom actions (Review, Add, Dismiss) ([iOS] `accessibilityAction`, [RN] `accessibilityActions`). Flagged field: "Year, 2027, assumed, no year on flyer. Needs review." The toast is announced, and its Undo is reachable (the timer pauses while it is focused). Thumbnails are labeled "Screenshot from Jan 10, flyer".
- **Reduced motion:** cross-fades replace slides, morphs and fly-ins; the skeleton is static; the onboarding demo is a still image. Feedback (check icon, toast, haptic) stays. In RN, Reanimated's `ReduceMotion.System` + `useReducedMotion`; in SwiftUI, `@Environment(\.accessibilityReduceMotion)`.
- Touch targets ≥ 44×44 pt (iOS) / 48 dp (Android); no meaning is carried by color alone; supports Bold Text and Dark Mode.

## 7. Implementation guidance

**Native components first** (cheap, accessible, platform-feeling): system sheets, pickers (date/time wheel or compact), lists, tab bar, share extension, photo picker.
- **SwiftUI build:** `NavigationStack`, `.sheet` + `presentationDetents`, `DatePicker(.compact)`, `ContentUnavailableView` for empties, `.sensoryFeedback(.success)`, SF Symbols, `matchedGeometryEffect` for the confirm morph. The rich notification needs a Notification Content Extension (platform-specific).
- **RN/Expo build:** Expo Router (native tabs/stack), `react-native-reanimated` + layout animations, `@gorhom/bottom-sheet` (or native formSheet in Expo Router), `@shopify/flash-list` for the 10k feed, `expo-image` for thumbnail caching, `@react-native-community/datetimepicker`, `expo-haptics`, `expo-symbols`. Avoid a full UI kit (NativeBase, etc.): our component set is small, and a custom token layer gives the premium look. Rich notification previews and the share extension still need native config plugins (flag this to the platform agent).

**Token structure in code** (single source → both platforms):
```
tokens/
  core.json      // raw: indigo600 "#4F46E5", space4 16, radiusLg 20
  semantic.json  // light/dark: accent → {light: indigo600, dark: indigo300}
  motion.json    // durShort 150, durMed 300, springDefault {damping 18, stiffness 220}
build: Style Dictionary → theme.ts (RN) and Theme.swift (SwiftUI)
```
Components consume only semantic tokens (`theme.color.flag.tint`), never raw hex. A unit test asserts that every text/background pair listed in the token file meets its contrast target.

**Verifying visual quality:**
1. **SCR-GALLERY** (debug-only screen): every CMP in every state (draft/flagged/confirmed/error), light/dark, at XS and AX3 text sizes, with reduced motion on and off. In RN this is Storybook for React Native, whose own docs say visual testing must come from other tools ([Storybook RN testing](https://storybookjs.github.io/react-native/docs/intro/testing)); in SwiftUI use `#Preview` variants.
2. **Snapshot tests:** [iOS] `swift-snapshot-testing` over the gallery matrix; [RN] story-driven Jest render tests (`composeStories`) for structure, plus Maestro screenshot flows on a simulator for pixels. Disable animations in tests.
3. **Flow scripts:** Maestro flows for the magic moment, deny-permission, offline, undo.
4. **Design review checklist** per PR: tokens only, all 5 states present, VoiceOver pass, reduced-motion pass, dark mode pass, 60 fps feed scroll on a mid-range device.

**Scope guard for January:** if time slips, cut in this order: the onboarding demo animation (use a still), field fly-in stagger, the rich notification expansion, then the search "Related" labeling. Never cut flags, undo, the draft/confirmed visual distinction, or the error/empty states.

## Stable ID index
Screens: SCR-ONBOARD (ONB-1..4), SCR-HOME, SCR-CONFIRM, SCR-SEARCH, SCR-DETAIL, SCR-HISTORY, SCR-SETTINGS, SCR-PRIVACY, SCR-STATES (ST-OFFLINE, ST-PERM-LIMITED, ST-SENSITIVE, ST-SERVER-ERR, ST-SLOW), SCR-GALLERY.
Components: CMP-THUMB, CMP-ACTIONCARD, CMP-FIELDROW, CMP-CHIP, CMP-SHEET, CMP-BTN, CMP-ROW, CMP-SEARCH, CMP-TOAST, CMP-BANNER, CMP-BADGE, CMP-SKELETON, CMP-EMPTY.

## Sources
- [Apple HIG: Privacy](https://developer.apple.com/design/human-interface-guidelines/privacy) · [Onboarding](https://developer.apple.com/design/human-interface-guidelines/onboarding) · [Playing haptics](https://developer.apple.com/design/human-interface-guidelines/playing-haptics) · [Feedback](https://developer.apple.com/design/human-interface-guidelines/feedback)
- [Material 3 motion: easing & duration](https://m3.material.io/styles/motion/easing-and-duration) (values cited via secondary refs; verify)
- [MacStories: Fantastical review](https://www.macstories.net/reviews/the-new-fantastical-review/) · [Daring Fireball on event creation UI](https://daringfireball.net/linked/2025/06/03/event-creation-still-largely-feels-like-an-unsolved-ui-problem) · [Things 3 review](https://lifestack.ai/blog/things-3-review)
- [Storybook for React Native: testing](https://storybookjs.github.io/react-native/docs/intro/testing)
- Apple screenshot actions/Pixel context: see FEATURES.md links (9to5Mac, Android Authority).
