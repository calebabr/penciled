# UI.md: Screenshot Actions beta UI (final, design only)

Status: final. Sources: FEATURES.md (incl. Round 4, F2f), raw/chair_decisions.md D1–D22 (authoritative), and the raw/2_*, 3_eval, 4_*, 5_ai files. Later decisions win (§7.8). Every element carries a stable ID (§8 index) and a tier: **core** (must-be-beautiful: polish, motion, dark mode, full a11y pass) or **plain** (system defaults, tokens for color only, no custom motion).

---

## 1. Design principles and visual direction

1. **Pencilled in until you tap; inked when added.** A Draft looks tentative (dashed Graphite border, casual title face). An added item looks committed (solid Ink border, linear face, check). This makes the core rule visible: the model proposes, code validates, the user confirms.
2. **Show the doubt, once, with a reason.** Two flag tiers only. *Blocking* flags (validation failure, weekday/date conflict, "12am", past date, resolve failure, Ask-state question) get a Highlighter mark behind the value plus a text reason. *Assumptions* (inferred year, inferred AM/PM, relative-date anchor) get a quiet Graphite caption that is tappable and does not block.
3. **The screenshot is the hero.** Every Draft sits beside its source. Checking a field means glancing at the image.
4. **Never wait on decoration.** The calendar write starts at the tap. Animation never gates it. Undo is always one gesture away.
5. **Honest by default.** Data flow before any permission ask; sensitive items say "Kept on this phone"; no "not stored" claim until verified (D3).

**Visual direction: "Pencil, highlighter, ink"** (D12). Cool Desk canvas, white Sheet, Graphite text and draft lines, one action color (Ink), one doubt color (Highlighter), Correction red for errors only. No green, teal, gradients, sparkle icons, chat bubbles or card shadows. Recursive appears only in the card and Confirm sheet; chrome is the system font.

**Vocabulary rules (D13).** Use exactly these words in UI, notifications, a11y labels and code enums:

| Concept | Word | Never |
|---|---|---|
| Unconfirmed item state | **Draft** | Proposal, Proposed, Suggestion |
| Home section of Drafts | **Ready to add** | READY, Inbox |
| Confirmed state | **Added** | Done, Confirmed, Saved |
| Throw away a Draft | **Dismiss** | Discard proposal, Delete (Delete is for data) |
| Gate state, low score | **Not sure** (badge) / "Needs a look" (internal) | Error, Failed |
| Calendar alarms | **alerts** | reminders, ladder |
| Sensitive / local | **Kept on this phone** | Private, Kept on device |
| Calendar-denied fallback log status | **Sent to Calendar** (no Undo: the app cannot confirm the user saved it, D22.6) | Added, Saved |
| Toast/snackbar | "toast" on iOS, "snackbar" on Android (same CMP-TOAST) | |

Copy style: sentence case; no all-caps section labels; no eyebrows; commas, not middle dots ("Fri, Jan 22, 7 PM"); the button names exactly what it writes, and the toast and History echo the same verb.

---

## 2. Design system

### 2.1 Color tokens (static scheme, no Dynamic Color in beta, D13)

| Token | Light | Dark | Use | Tier |
|---|---|---|---|---|
| `color.desk` | #E8EBEE | #14171B | screen canvas | core |
| `color.sheet` | #FFFFFF | #1D2126 | cards, sheets, rows | core |
| `color.sheetRaised` | #FFFFFF | #262B31 | sheet over sheet, dialogs | plain |
| `color.sunken` | #DDE1E6 | #101316 | search field, idle chips | plain |
| `color.graphite` | #2A2E35 | #E4E7EB | primary text; Draft dashed border | core |
| `color.graphiteSoft` | #5A616B | #A3AAB4 | secondary text, captions (≥4.5:1 on desk and sheet) | core |
| `color.hairline` | #CDD3D9 | #343A42 | dividers (decorative, no contrast duty) | plain |
| `color.ink` | #22398F | #9EB3FF | the only action color; Added border/check; links | core |
| `color.onInk` | #FFFFFF | #14171B | text/icons on Ink | core |
| `color.inkFlood` | #22398F @ 14% | #9EB3FF @ 18% | transient ink-in flood only | core |
| `color.highlighter` | #FFE36E | #5A4A0C | blocking-flag mark fill (behind value text) | core |
| `color.onHighlighter` | #2A2E35 | #FFE36E | value text on the mark | core |
| `color.correction` | #B3261E | #F2B8B5 | errors, destructive text | plain |
| `color.toastBg` | #2A2E35 | #E4E7EB | inverted toast/snackbar | core |
| `color.toastText` | #FFFFFF | #14171B | toast text; toast action uses `ink` dark/light inverse (#9EB3FF / #22398F) | core |

Estimated contrast (the unit test in §7.5 is the source of truth): Ink on Sheet ≈ 10:1 light, ≈ 8:1 dark; graphiteSoft on Desk ≈ 5.2:1, on dark Sheet ≈ 6.9:1; onHighlighter on Highlighter ≈ 11:1 light, ≈ 6.8:1 dark; Correction on Sheet ≈ 6.5:1. Non-text: the dark-mode Highlighter mark (#5A4A0C on #1D2126) is below 3:1, so the mark is never the only signal: a flag icon and a reason line always accompany it.

**Increase Contrast set** (iOS "Increase Contrast" / Android "High contrast text"; no React Native detection API confirmed, **verify**; where none exists, the set is not applied and the base palette, which already meets 4.5:1, is used): borders 1.5 → 2 pt; `graphiteSoft` → `graphite`; `hairline` → `graphiteSoft`; `inkFlood` alpha doubled.

Calendar color dot: next to "Added to Personal" show the user's calendar color as an 8 pt dot, always beside the calendar name (never color alone). It is data, not a palette token.

### 2.2 Typography

| Token | Font | Size/line | Weight | Use | Tier |
|---|---|---|---|---|---|
| `type.cardTitleDraft` | Recursive Sans **Casual** | 20/26 | 600 | card + sheet title, Draft state only | core |
| `type.cardTitle` | Recursive Sans **Linear** | 20/26 | 600 | same text once Added, and read-only view | core |
| `type.dateLine` | Recursive Sans Linear, tabular figures | 22/28 | 600 | the date/time line, **both states** | core |
| `type.fieldValue` | Recursive Sans Linear, tabular figures | 17/22 | 500 | field values (dates, times, location) | core |
| `type.largeTitle` | system | 34/41 | 700 | "Screenshots" header | plain |
| `type.headline` | system | 17/22 | 600 | section titles, row titles | plain |
| `type.body` | system | 17/22 | 400 | body, buttons (600) | plain |
| `type.callout` | system | 16/21 | 400 | banners, question lines | plain |
| `type.footnote` | system | 13/18 | 400 | captions, assumptions | plain |
| `type.caption` | system | 12/16 | 500 | badges, field labels | plain |

Rules (D12, Impeccable P1): Casual never sets digits, dates or times; title only, Draft only. All sizes scale with Dynamic Type / font scale. Three static instances (Casual 600, Linear 600, Linear 500), ~150–200 KB. Verify `@expo-google-fonts/recursive` ships Casual statics; otherwise instance once with fonttools and commit the TTFs. Verify `fontVariant: ['tabular-nums']` works with the bundled files; fallback is the system font with tabular-nums for `dateLine`/`fieldValue`. Test both faces at 200% before committing.

### 2.3 Spacing, radii, borders, elevation, icons

| Group | Tokens |
|---|---|
| Spacing (4-pt) | `space.1` 4, `2` 8, `3` 12, `4` 16 (screen gutter), `5` 20, `6` 24, `8` 32, `10` 40 |
| Radii | `radius.sheet` 28 (system), `radius.card` 16, `radius.button` 12 (not pills), `radius.field` 10, `radius.thumb` 6, `radius.mark` 3, `radius.chip` full |
| Borders | `border.draft` 1.5 pt dashed graphite; `border.added` 1.5 pt solid ink; Increase Contrast 2 pt |
| Elevation | `elev.0` flat (cards, rows; state lives in the border); `elev.sheet` system sheet shadow; `elev.toast` y4 blur16 #000 18% (light only; dark uses inverted surface) |
| Hit targets | `hit.min` 44 pt iOS / 48 dp Android |
| Icons | SF Symbols on iOS (`expo-symbols`), Material Symbols Rounded on Android; 20 pt inline, 24 pt nav; text label on every action that matters |

### 2.4 Component library

| ID | Component | Spec | Tier |
|---|---|---|---|
| CMP-THUMB | Screenshot thumbnail | cover-crop for any aspect ratio, `radius.thumb`, hairline border; loads the pre-generated small file made at ingest (never the full image in grids); status shape: Draft = dashed graphite outline, Added = small solid Ink corner tick; Not sure / Kept on this phone / Nothing to do = CMP-BADGE overlay; a11y label carries the status | core |
| CMP-ACTIONCARD | Draft card | thumbnail left (64 × 128 cover), right: state label "Draft", title (`cardTitleDraft`), date line, up to 2 field lines, flag/assumption line, buttons [Dismiss] (tertiary) and [Review] (primary; opens SCR-CONFIRM, where Add lives). No card ever writes directly (D20): the card shows at most 2 field lines, so end, calendar and alerts would be hidden. Up to 3 sub-actions from one screenshot (event + deadline), each with a checkbox (default on). Variants: ST-GATE-READY, ST-GATE-ASK, ST-ADDED (compact inked row: title Linear, date, "Added to Personal" + dot + [Undo]), ST-UNDONE (back to Draft). At font scale ≥ 1.6 it stacks (thumb on top). | core |
| CMP-FIELDROW | Editable field row | label (`caption`, graphiteSoft) over value (`fieldValue`). Variants: normal; **blocking** (Highlighter mark behind value text only, flag icon, reason line, optional one-line question, [Looks right] text button); **assumption** (Graphite caption with info icon, e.g. "Year: 2027, inferred", tap opens picker); **missing** ("Not found in screenshot", empty, required ones block); **relative anchor** ("Relative to Wed, Nov 18 ▾"). Tap value opens native picker inline. Long-press shows source quote ("from: 'Fri 7 @ Student Ctr'") if the schema returns one. | core |
| CMP-CHIP | Chip | pill, 32 pt visual / 44–48 hit; idle/selected/disabled. Two uses: alert chips ("Day before, 6 PM ✓", "Morning of, 9 AM ✓", "Custom"), disabled with "Already passed"; filter chips on Home. | plain |
| CMP-SHEET | Confirm container | Expo Router native `formSheet` (detents medium/large, grabber) preferred; `@gorhom/bottom-sheet` only if formSheet fails the spike (screen-reader focus issues reported by the community, **verify** in SP-14) | core |
| CMP-BTN | Buttons | Primary: filled Ink, 50 pt, `radius.button`, full width in sheets; label always says what it writes. Secondary: Ink outline. Tertiary: Ink text. Destructive: Correction text. Pressed: scale 0.97. Never visually disabled for open flags (see SCR-CONFIRM). | core (primary), plain (rest) |
| CMP-INKIN | Ink-in overlay | one absolute `Animated.View` clipped to the card; see §3 | core |
| CMP-TOAST | Toast (iOS) / Snackbar (Android) | bottom, above safe area, `toastBg`, message + one action ([Undo]); **8 s**, paused while touched or focused by a screen reader; announced | core |
| CMP-BANNER | Inline banner | full width, icon + one sentence + up to 2 text actions; variants info / warn / error / offline / private | plain |
| CMP-BADGE | Status badge | small pill: Draft, Added, Not sure, Reading…, Waiting, Couldn't read, Nothing to do, Past date, Kept on this phone (lock icon) | plain |
| CMP-ROW | List row | 56–72 pt; leading thumb/icon, title, subtitle, trailing value/chevron/[Undo]; swipe actions | plain |
| CMP-GRID | Library grid | 3 columns, FlashList v2 (fallback v1 or FlatList + `getItemLayout`), CMP-THUMB cells | plain |
| CMP-SEARCH | Search field | `sunken` field, magnifier, placeholder "Search your screenshots"; FTS5 keyword only | plain |
| CMP-SKELETON | Pencil skeleton | static dashed graphite lines in the shape of field rows; no shimmer | plain |
| CMP-EMPTY | Empty state | system icon (not illustration), title, one sentence, one button | plain |
| CMP-DATAFLOW | Data-flow diagram | Phone → "Text is sent to [provider] to read it" → "[verified retention]" → Your calendar; lock row for kept-on-phone types; reused in Settings › Privacy | core |
| CMP-COACH | Share-sheet coach | 3 annotated real screenshots of the iOS share sheet (Share → More → Edit → add to Favorites) | plain |
| CMP-NOTIF | Notification templates | Android only in beta; see §4.5 | plain |
| CMP-DIALOG | System alert | native Alert for destructive/guard confirms only | plain |

---

## 3. Motion and haptics

Each segment ≤ 350 ms; one sequence ≤ 700 ms; nothing loops; springs `withSpring({damping: 18, stiffness: 220})` or `withTiming` with standard ease `cubic-bezier(0.2, 0, 0, 1)` (M3 easing reference: https://m3.material.io/styles/motion/easing-and-duration, verify values). Haptics only for confirm, undo, error, selection (Apple's haptics guidance, claim about overuse unconfirmed, **verify** via the `.md` URL: https://developer.apple.com/design/human-interface-guidelines/playing-haptics).

| Moment | Motion | Haptic | Tier |
|---|---|---|---|
| **Add (ink-in)** | Write starts at tap (≤ 500 ms tap-to-write-started). (1) Button label → ✓, 120 ms. (2) Ink circle scales from the tap point, clipped by the card, 260 ms ease-out; at 50% the border swaps dashed→solid Ink and the title re-sets Casual→Linear. (3) Flood "dries" to 0 while the card compacts to the Added row, 300 ms. Total ≈ 680 ms. Toast rises when both the compact and the write success have happened. | success at flood start | core |
| Write fails | Sequence plays in reverse (or stops and reverses mid-way); card is Draft again with edits kept; error banner slides in | error | core |
| Undo (un-ink) | Reverse flood, card returns to Draft (not removed); toast swaps to "Removed from Personal" | light impact | core |
| Looks right / flag fixed | Highlighter mark fades out 200 ms; flag icon swaps to check (no morph) | selection | core |
| Card arrives | fade + 12 pt slide down, 250 ms; siblings via layout animation | none | core |
| Toast | rise 200 ms, fall 150 ms | none | core |
| Sheet | system formSheet spring | system | plain |
| Reading | static "Reading…" badge, pencil skeleton rows; no pulse | none | plain |

Cut (rebuttal): field fly-in stagger, amber wipe, ⚠→✓ morph, processing pulse ring, onboarding demo loop.

**Reduced motion:** the ink-in becomes a 150 ms cross-fade between Draft and Added; card arrival and toast cross-fade; haptics, check icon and toast stay. Use Reanimated `useReducedMotion()` / `ReduceMotion.System`.

Haptics via `expo-haptics` (`notificationAsync`, `impactAsync(Light)`, `selectionAsync`); verify the Android mapping on a mid-range device.

---

## 4. Screens and states

Four screens only (D11): SCR-ONBOARD, SCR-HOME, SCR-CONFIRM, SCR-SETTINGS. No tab bar. Home is the root; Confirm is a sheet over Home; Settings is a pushed stack screen.

### 4.1 SCR-ONBOARD (plain shell; ONB-2 core)

One decision per screen (D13). Skippable only after ONB-2 (data flow must be seen before any permission ask, F7a).

| ID | Screen | Platform | Content | Tier |
|---|---|---|---|---|
| ONB-1 | Value | both | still image of a flyer becoming a Draft card. "Screenshots that turn into plans." [Continue] | plain |
| ONB-2 | Data flow | both | CMP-DATAFLOW. Copy (final wording after D3 spike): "Text from your screenshot is sent to our server and to [provider] so we can read it. Our server keeps the result in memory for up to 10 minutes, then forgets it; it never saves your text. [Verified provider retention sentence.] Names in chat screenshots are sent. Banking, passwords, IDs and health screens stay on this phone (English only for now). You approve everything. Nothing is added without your tap." [Continue] [How this works] | core |
| ONB-3 | Try it | both | bundled sample flyer; tap → real Confirm sheet with sample data (Ask variant, one highlighted field) → Add plays ink-in, writes nothing ("Sample, nothing was added"). | plain |
| ONB-4 | Photos | both | Android: "Notice new screenshots without opening the app." iOS: "Find new screenshots each time you open the app." [Allow access] → system prompt. [Not now] | plain |
| ONB-5 | Notifications | Android only | "Get a heads-up when a screenshot is ready to add." [Turn on] → system prompt. [Not now] | plain |
| ONB-6 | Share sheet coaching | iOS only | CMP-COACH: "Add us to your share sheet. It takes 20 seconds and makes sharing one tap." Steps with real screenshots: take a screenshot, tap the thumbnail, Share, scroll to More, Edit, add to Favorites. [Done] [Show me later] | plain |

Order: iOS 1 → 2 → 3 → 4 → 6. Android 1 → 2 → 3 → 4 → 5. Calendar is never asked here; it is asked at the first real Add with a one-line pre-explainer (iOS: "Full access lets you undo." D7).

```
ONB-2 (core)                     ONB-6 (iOS)
┌──────────────────────────┐    ┌──────────────────────────┐
│ How it works             │    │ Add us to your share     │
│                          │    │ sheet                    │
│ [phone] Screenshot       │    │ ┌──────────────────────┐ │
│    │  text only          │    │ │ [real share sheet,   │ │
│    ▼                     │    │ │  "More" circled]     │ │
│ [cloud] [Provider] reads │    │ └──────────────────────┘ │
│    │  [retention text]   │    │ 2 of 3  Tap Edit, then + │
│    ▼                     │    │ next to Screenshot       │
│ [cal] Your calendar,     │    │ Actions.                 │
│       only after you tap │    │                          │
│ [lock] Banking, IDs,     │    │ [ Next ]                 │
│  health: stay on phone   │    │   Show me later          │
│ [ Continue ]             │    └──────────────────────────┘
│   How this works         │
└──────────────────────────┘
```

States:
- ST-PERM-PHOTOS-DENIED: Home banner "Auto-detect is off. Share screenshots to us instead. [How] [Settings]". Never silent (F1c).
- ST-PERM-PHOTOS-LIMITED (iOS "Selected photos"; Android 14+ "Selected photos" partial access): banner "With selected photos we can't see new screenshots. Share them to us, or allow all photos. [How] [Settings]". On Android the auto-detect worker stays off while access is partial.
- ST-PERM-NOTIF-OFF (Android): banner "Notifications are off, so you'll only see Drafts when you open the app. [Turn on]".
- Skip after ONB-2 lands on Home with the relevant banners.

### 4.2 SCR-HOME (incl. search, Added filter, swipe-undo)

Layout top to bottom: large title "Screenshots" with [+] (import, system picker, `selectionLimit` 20) and [gear] (Settings); banner slot (one banner at a time, priority: error > offline > permission > catch-up); **Ready to add** section: up to 3 CMP-ACTIONCARDs stacked, then "See all 5" (applies the Drafts filter); **Library**: CMP-SEARCH, filter chips **All · Drafts · Added · Not sure**, then CMP-GRID.

```
Default                              Added filter (list mode)
┌──────────────────────────┐        ┌──────────────────────────┐
│ Screenshots         +  ⚙ │        │ Screenshots         +  ⚙ │
│ Ready to add             │        │ [Search your screenshots]│
│ ┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐│        │ All  Drafts (Added) Not s│
│  ▯ Draft                 │        │ ┌──────────────────────┐ │
│  ▯ Pizza Night  (casual) │        │ │▯ Pizza Night         │ │
│  ▯ Fri, Jan 22, 7 PM     │        │ │  Fri, Jan 22, 7 PM ✓ │ │
│  ▯ ▐Date▌ 1 to check     │        │ │  ● Personal   [Undo] │ │
│    Dismiss   [Review]    │        │ └──────────────────────┘ │
│ └ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘│        │  ◀ swipe left: Undo      │
│ Library                  │        │ ┌──────────────────────┐ │
│ [Search your screenshots]│        │ │▯ Essay due           │ │
│ (All) Drafts Added Not su│        │ │  Tue, Dec 1, 11:59 PM│ │
│ ▯ ▯ ▯                    │        │ │  ● School     [Undo] │ │
│ ▯ ▯ ▯                    │        │ └──────────────────────┘ │
└──────────────────────────┘        └──────────────────────────┘
```

Card button logic (D20): Ready → [Dismiss] [Review]; Ask → "1 to check" + [Dismiss] [Review]. Add lives only in the sheet, where every field is visible. Minimum path from a Ready card: Review, then Add (2 taps).

**Search (plain):** typing filters the Library by FTS5 (trigram) within the active chip; Ready collapses while a query is active. Results stay as tiles (no snippets in beta). Spinner only after 150 ms; p95 ≤ 300 ms at 10k.

**Added filter + swipe-undo (core):** the Added chip switches the grid to inked CMP-ROW list mode. Swipe left reveals [Undo]; long-press on an Added tile in grid mode opens [Undo add] [Delete screenshot data]. Both are accessibility actions too. The full log stays in Settings › History.

**Tap behavior:** Draft, Not sure and Couldn't read (ST-BASIC) → SCR-CONFIRM editable (Not sure and Couldn't read = manual entry). Added, Nothing to do, Kept on this phone → read-only view.

States:
| ID | Treatment | Tier |
|---|---|---|
| ST-EMPTY-NEW | Android: CMP-EMPTY "Take a screenshot of a flyer or plan. It'll show up here." [Import a screenshot]. iOS: "Share a screenshot to us, or it'll be found next time you open the app." [Show me how] (reopens CMP-COACH) [Import] | plain |
| ST-LOADING | 6 skeleton tiles; Ready section hidden until loaded | plain |
| ST-READING | tile shows static "Reading…" badge; a share/import shows a pencil-skeleton card in Ready within 1 s | core (card) |
| ST-SLOW | after 8 s: "Taking longer than usual…" on the card | plain |
| ST-CATCHUP (iOS) | banner "Found 3 new screenshots. Reading them now." Processing starts automatically on open (no tap); tiles show "Reading…". Only screenshots after the install watermark; never before install. Images for catch-up items follow the "Auto-detected" switch (opt-in) | plain |
| ST-IMPORT-CAP | picker capped at 20; overflow: "We read up to 20 at a time. The first 20 are on their way." | plain |
| ST-DUPLICATE | no second item; toast "Already in your library", scroll to it | plain |
| ST-NOTHING | lands silently in Library with "Nothing to do" badge; no card, no notification (F2d). Read-only view offers [Read again] | plain |
| ST-GATE-NEEDSLOOK | no card, no push; tile gets "Not sure" badge; visible via the Not sure chip | plain |
| ST-SENSITIVE | tile badge "Kept on this phone" (lock); no card; searchable locally; read-only view offers an optional [Add manually] that opens a blank Confirm sheet (nothing pre-filled, nothing sent) | plain |
| ST-OFFLINE | banner "You're offline. New screenshots will be read when you reconnect." Tiles show "Waiting". Search still works. Offline waits don't use up retries. | plain |
| ST-SERVER-ERR | tile badge "Reading…" stays while the pipeline makes up to 3 automatic calls (initial + 2 retries, backoff); silent until the 3rd call fails, then the item becomes ST-BASIC | plain |
| ST-BASIC | after 3 failed calls (or "too large"): tile badge "Couldn't read"; no push; opens SCR-CONFIRM in manual entry: title pre-filled from the first OCR line, the dated OCR line shown as a caption ("Screenshot says: 'Fri 7 @ Student Ctr'"), every field blocking; [Try again] in the sheet makes one new call | plain |
| ST-PAUSED | provider budget cap reached (503): banner "Reading is paused for now (beta limit). Your screenshots are saved and will be read later." Paused time doesn't use up retries. | plain |
| ST-UPGRADE | server says the app is too old (426): banner "Update the app to keep reading screenshots. [Update]"; items wait as "Waiting" | plain |
| ST-RESTORED-MISSING | after a phone restore, a row whose image isn't on this phone: tile shows a blank thumbnail with "Image not on this phone"; fields and history still open read-only | plain |
| ST-AUTODETECT-FALLBACK | Android build without a working app-closed pipeline (F1 week-2 gate): Android shows the iOS model, catch-up banner + share coaching copy | plain |
| ST-SEARCH-NONE | "Nothing matched. Try fewer words." | plain |
| ST-SEARCH-EMPTY-QUERY | chips + full grid; placeholder hint "Try 'pizza' or 'dentist'" | plain |
| ST-ADDED-EMPTY | Added chip with nothing: "Nothing added yet. Things you add show up here, and you can undo them." | plain |

### 4.3 SCR-CONFIRM (incl. read-only view) (core)

CMP-SHEET at large detent. Top: screenshot (pinch-zoom, ~40% height). Bottom: state label, title, date line, field rows, assumption captions, the anchor caption, calendar picker with color dot, alert chips, primary button, [Dismiss].

```
Draft, Ask state (core)               Read-only (Added)
┌──────────────────────────┐        ┌──────────────────────────┐
│ ▔▔▔                      │        │ ▔▔▔                      │
│ [   screenshot, zoom   ] │        │ [   screenshot, zoom   ] │
│ Draft                    │        │ Added ✓                  │
│ Pizza Night   (casual)   │        │ Pizza Night   (linear)   │
│ Fri, Jan 22, 7 PM        │        │ Fri, Jan 22, 7 PM        │
│ ⓘ Year: 2027, inferred   │        │ Student Center           │
│ ⓘ Relative to Wed, Nov 18▾│       │ ● Added to Personal,     │
│ ⓘ Time: 7 PM, assumed    │        │   Nov 18, 9:41 AM        │
│ ⚑ Date ▐ Fri, Jan 22 ▌   │        │ RSVP deadline, Wed,      │
│   Flyer says "Thu Jan 22"│        │   Jan 20, alerts: day    │
│   Jan 22 is a Friday.    │        │   before 6 PM, morning   │
│   [Looks right]          │        │   of 9 AM                │
│ Where  Student Center    │        │ Kept: text only sent     │
│ Calendar ● Personal ▾    │        │                          │
│ ☑ RSVP deadline, Wed,    │        │ [ Undo add ]             │
│   Jan 20                 │        │ ⋯ Delete screenshot data │
│ Deadline alerts          │        └──────────────────────────┘
│ (Day before ✓)           │
│ (Morning of ✓)(Custom)   │
│ [ Check date to continue]│
│        Dismiss           │
└──────────────────────────┘
```

Behavior:
- Focus lands on the first blocking flag; blocking rows sort first.
- **Primary button never looks disabled (D13).** With open blocking flags it reads "Check date to continue" (names the first one); tapping scrolls to and briefly outlines that row. When all are resolved it reads exactly what it writes: "Add event", "Add event + deadline", "Add deadline + 2 alerts".
- "Looks right" accepts a flagged value without editing; editing also resolves it.
- Missing fields show "Not found in screenshot" and are never filled with placeholder data.
- Alert chips (one calendar item, up to 3 alerts: day before 18:00, morning of 09:00, one custom; F5). Presets are pre-selected for **deadlines only**, under the label "Deadline alerts"; an event starts with no alerts and shows an "Add alert" chip (D20). Chips in the past are disabled with "Already passed". For an all-day deadline, the morning-of chip stays valid until 23:59 on the due date.
- Dismiss → sheet closes, card leaves Ready, toast "Dismissed. [Undo]" (no side effects, F4e).
- iOS: swipe-down closes (Draft and edits kept). **Android: system Back closes the sheet**; if edited, guard dialog "Keep your edits?" [Keep editing] [Close and keep draft]. Only Dismiss throws a Draft away. Support predictive back where Expo Router provides it (https://developer.android.com/guide/navigation/custom-back/predictive-back-gesture, verify).

**Gating states (F2f, D17)** reuse CMP-ACTIONCARD + CMP-FIELDROW; no new screen:

| ID | Rule (server-provided `gate_state`) | Card | Sheet | Push (Android) |
|---|---|---|---|---|
| ST-GATE-READY | card score ≥ 0.90, every required field grounded | [Review] on card (D20; no Add on the card) | Add enabled; assumption captions non-blocking | one "Ready to add" push, [Review] only |
| ST-GATE-ASK | 0.60 ≤ card score < 0.90 | "1 to check" + [Review] | each Ask field is a blocking row with a one-line question; Add reachable only after each is touched | "N things to check" push, [Review] only |
| ST-GATE-NEEDSLOOK | card score < 0.60, or class unsure | none; Library "Not sure" | fields flagged or blank for manual entry; Add after required fields are filled | none |

Card score = the minimum over required fields (title, date/time) and class confidence; an optional field (end, location) under 0.60 shows as "Not found in screenshot" instead (DESIGN §5.5).

Hard overrides beat all three: ungrounded field can never be Ready; ST-SENSITIVE (local-only, no cloud proposal, no card; read-only view with local text and "Kept on this phone because it looks like [banking]. Nothing was sent." plus optional [Add manually] → blank sheet); ST-PAST (the one past rule: no push, no Ready card, Library tile under Drafts with a "Past date" badge, counted in F8 (D21); in the sheet the date row is blocking with "This date has passed. Pick a new date." and Add stays blocked until a future date is picked; there is no "already happened" option); ST-RESOLVE-FAIL (date row blocking: "Couldn't work out the date. Pick it."). These states render the same in every gate.

Other states:
| ID | Treatment | Tier |
|---|---|---|
| ST-ASSUMPTION | Graphite caption + info icon; tap opens picker; non-blocking | core |
| ST-BLOCKING | Highlighter mark, flag icon, reason, optional question, [Looks right] | core |
| ST-PERM-CAL-PREASK | first Add: one-line pre-explainer above the button ("We'll ask for Calendar. Full access lets you undo.") then the system prompt | plain |
| ST-PERM-CAL-DENIED | banner in sheet: "Calendar access is off. Turn it on in Settings, or add it with the share sheet." [Open Settings] [Open in Calendar] [Share as file]; Draft kept. [Open in Calendar] hands the fields to the system editor (iOS) or the calendar insert screen (Android); the item is then logged as "Sent to Calendar" (not "Added": the app cannot know the user saved it; no Undo; D22.6) | plain |
| ST-ALREADY-ADDED | proposal-level duplicate (same title, start within 30 min of an Added item): card caption "Looks like you already added this" with [Review] still available; no push. In the sheet, Add first shows CMP-DIALOG "Add again?" (D21) | plain |
| ST-RECONCILE | after a crash or relaunch mid-write, if the item can't be found: Draft again with banner "We couldn't confirm this was added. Check and tap Add again." (never written without a fresh tap) | plain |
| ST-CAL-WRITEONLY (iOS) | Add works; toast "Added to Calendar. Undo isn't available with write-only access. [Open Calendar]"; read-only view shows "Added (can't undo from here)" | plain |
| ST-NO-CALENDAR | "No calendar can accept new events. Pick another, or share as a file." + picker | plain |
| ST-WRITE-FAILED | reverse ink-in; banner "Couldn't add to Calendar. Nothing was changed, and your edits are saved." [Try again] | core |
| ST-SYNC-PENDING | Added normally; caption "May take a moment to appear on other devices" | plain |
| ST-UNDO-BLOCKED | dialog "You changed this event after we added it. Delete it anyway?" [Delete it] [Keep it]; Keep → "No longer managed here" | plain |
| ST-READING (sheet) | pencil skeleton rows; fields fill as they arrive | core |
| ST-SAMPLE | ONB-3 sample: a "Sample" label; Add writes nothing | plain |

**Read-only view (plain layout, core typography):** for Added, Nothing to do, Kept on this phone. Screenshot, fields in Linear, action line (time, calendar), what was sent ("Text only sent" / "Text and image sent" / "Kept on this phone"), [Undo add] when Added; [Add manually] when Kept on this phone (blank sheet); overflow [Read again] (Nothing to do) and [Delete screenshot data] (CMP-DIALOG: "Deletes this screenshot's data from this phone". The server stores nothing per screenshot beyond a 10-minute in-memory result, so the copy never says "and our server" for one item).

### 4.4 SCR-SETTINGS (incl. Privacy + History) (plain)

Grouped native list (iOS inset grouped; Android M3 list), CMP-ROW only.

```
┌──────────────────────────┐
│ ‹ Settings               │
│ Capture                  │
│  Auto-detect   On ›      │  (Android) / Share sheet setup › (iOS)
│  Notifications On ›      │  (Android)
│ Calendar                 │
│  Default calendar ● Pers.│
│  Deadline alerts 2 ›     │
│ Privacy                  │
│  How your data is used › │  CMP-DATAFLOW + "What leaves this phone"
│  Keep message screenshots│
│   on this phone only [ ] │
│  Send image when text    │
│   isn't enough           │
│   Shared/imported   [on] │
│   Auto-detected    [off] │  (both: Android auto-detect, iOS catch-up)
│  Beta counts (never      │
│   content)          [on] │
│ History                  │
│  Added ‹Pizza Night›     │
│   Nov 18, Personal [Undo]│
│  See all ›               │
│ Delete all my data       │  (Correction text)
│ About · Send feedback    │
└──────────────────────────┘
```

- **Capture:** Android auto-detect On / Limited / Off with a fix link; iOS "Share sheet setup" reopens CMP-COACH: "We can't see screenshots while the app is closed. We check for new ones when you open it."
- **Optional "Pro preview" row (added: pricing pass); D25; first to cut:** a plain CMP-ROW (under About) that opens a plain info page; no new screen type and no purchase control. Honesty copy: "Not available in beta. Everything you use today stays free."
- **Calendar:** "Deadline alerts" sets which presets are pre-selected for deadlines (events start with none, D20).
- **Privacy:** data-flow diagram; "What leaves this phone" (redacted text; names in chats; images only per the toggles; never sensitive screens; our server keeps results in memory for up to 10 minutes and never saves them); chat toggle (D1, default off; covers anything that looks like a chat, even when unsure); image toggles (default on for shared/imported except sensitive and chat; off for auto-detected, which includes iOS catch-up). On Android every toggle takes effect for the background worker before the switch shows its new state. **No** sensitive-guard toggle, **no** "Send anyway".
- **History:** reverse-chronological CMP-ROWs grouped by day: "Added Pizza Night to Personal" + thumb + [Undo] (becomes "Undone" or "Released"); the calendar-denied Open-in-Calendar path logs **"Sent to Calendar"** with no Undo, because the app cannot confirm the user saved it (D22.6). Empty: "Nothing added yet. Things you add show up here, and you can undo them."
- **Delete all my data:** CMP-DIALOG "Delete everything? This removes all screenshots' data from this phone [and our server]. It can't be undone." [Delete everything] → result screen "Deleted from this phone [and our server]."
- States: ST-OFFLINE on delete-all ("We'll finish deleting from our server when you're back online", local wipe happens now); ST-HISTORY-EMPTY.

### 4.5 Notification design (CMP-NOTIF; Android only in beta)

iOS asks no notification permission in beta (FEATURES Round 4: iOS 2 permissions); alerts for events come from the calendar app itself.

| ID | When | Title / body | Actions |
|---|---|---|---|
| NTF-READY | ST-GATE-READY, one per card | "Ready to add" / "Pizza Night, Fri, Jan 22, 7 PM" + BigPicture thumbnail | [Review] only (Chair decision D19: the user sees the fields before anything is written; no one-tap add from the notification in beta) |
| NTF-CHECK | ST-GATE-ASK | "1 thing to check" / "Pizza Night, Fri, Jan 22" (N = flagged fields; grouped summary "3 screenshots to check" when > 2 are pending) | [Review] only |
| (none) | Needs a look, Nothing to do, sensitive, duplicates, resurfacing | no push. No resurfacing pushes in beta (D15); shadow "would-nudge" log only | |

Channels: "Ready to add" and "Things to check" (default importance) so testers can mute one. Tapping any notification deep-links to SCR-CONFIRM over Home.

### 4.6 Android vs iOS differences

| Topic | iOS | Android |
|---|---|---|
| Capture | share extension + catch-up on open (ST-CATCHUP) | MediaStore auto-detect (WorkManager) + share/import; fallback to iOS model |
| Permissions / onboarding | Photos (ONB-4), ONB-6 coaching, Calendar full at first Add | Photos, Notifications (ONB-5), Calendar at first Add |
| Confirm dismiss | swipe down | system Back with dirty-state guard |
| Toast naming | toast | snackbar (M3: https://m3.material.io/components/snackbar, verify) |
| Color | static scheme | static scheme, Dynamic Color off |
| Sheet | native formSheet | native formSheet (verify Android parity in Expo Router; else gorhom) |
| Notifications | none in beta | NTF-READY / NTF-CHECK, [Review] only (D19) |
| Undo without full access | write-only, no undo | n/a (READ_CALENDAR + WRITE_CALENDAR are expected to show as one Calendar prompt; **verify** on device in SP-8) |

---

## 5. The magic moment, frame by frame

Targets (FEATURES Round 4): "Reading…" card within 1 s of share; action card p50 5 s / p95 10 s end to end; ≤ 2 taps to Added with no flags (notification or card [Review], then Add), ≤ 3 with one flag (Review, Looks right, Add). There is no one-tap Add from a card or notification in beta (D19, D20). The demo flag is a weekday/date conflict; missing AM/PM is only an assumption caption (D20).

### 5.1 Android notification path

| # | Time | Frame |
|---|---|---|
| A0 | 0 s | User screenshots a club flyer in Instagram. Nothing interrupts. |
| A1 | ~5 s (p50) | NTF-CHECK: "1 thing to check / Pizza Night, Fri, Jan 22" with thumbnail and [Review]. (A Ready card instead shows NTF-READY with [Review] only; D19.) |
| A2 | tap | App opens; SCR-CONFIRM rises over Home. Card is Draft: dashed border, Casual title, Linear date line. |
| A3 | +0 | Focus on the Date row: Highlighter behind "Fri, Jan 22", reason "Flyer says 'Thu Jan 22'. Jan 22 is a Friday." Captions above: "Year: 2027, inferred", "Time: 7 PM, assumed" (non-blocking). Button reads "Check date to continue". |
| A4 | tap | [Looks right]: mark fades (200 ms), selection haptic. Button becomes "Add event + deadline". |
| A5 | tap | First real Add only: Calendar pre-explainer line, system prompt. Then write starts; ink-in plays (≈ 680 ms), success haptic at the flood. |
| A6 | +0.7 s | Sheet closes; Ready card is the compact inked row. Snackbar: "Added event + deadline to Personal [Undo]" for 8 s. |
| A7 | later | Home › Added shows the row with swipe Undo; Settings › History logs it. |

### 5.2 iOS share-sheet path

| # | Time | Frame |
|---|---|---|
| I0 | 0 s | User screenshots a group-chat plan; taps the screenshot thumbnail, then Share. |
| I1 | tap | Our app is in Favorites (coached by ONB-6). Tap it; the app opens via the share extension (must pass SP-3 "opens unaided"; if not, the extension shows "Saved. Open the app to review." and I2 starts when the user opens the app). |
| I2 | ≤ 1 s | Home with a pencil-skeleton card in Ready to add, badge "Reading…" (ST-READING). |
| I3 | ~5 s | Fields fill in; the card is Draft. A Ready card shows [Review] (tap opens SCR-CONFIRM); an Ask card opens SCR-CONFIRM automatically with focus on its question row. |
| I4 | tap | Resolve the Date flag ("Flyer says 'Thu Jan 22'. Jan 22 is a Friday." → [Looks right]), as A4. |
| I5 | tap | First Add: "We'll ask for Calendar. Full access lets you undo." → system prompt (Full). Ink-in, success haptic. |
| I6 | +0.7 s | Toast "Added event to Personal [Undo]" 8 s. If the user granted write-only: ST-CAL-WRITEONLY toast. |
| I7 | next open | Screenshots not shared since last open are read automatically; ST-CATCHUP banner "Found 3 new screenshots. Reading them now." |

---

## 6. Accessibility requirements

| ID | Requirement |
|---|---|
| A11Y-01 | Every control has a role and label. Card label: "Draft event, Pizza Night, Friday January 22, 7 PM, Student Center. 1 thing to check." Added: "Added event, Pizza Night, … to Personal." |
| A11Y-02 | Card actions exposed as custom accessibility actions: Review, Dismiss, Undo (Add exists only inside the Confirm sheet, D20). Swipe and long-press actions on Home are also accessibility actions. |
| A11Y-03 | State is never color- or shape-only: Draft/Added are words in the label; flags carry an icon and a reason; thumbnail status (dashed vs tick) is repeated in the label; calendar dot sits beside the name. |
| A11Y-04 | Contrast: text ≥ 4.5:1, large text and meaningful non-text ≥ 3:1, both themes, enforced by the token test (WCAG 2.1 1.4.3: https://www.w3.org/TR/WCAG21/#contrast-minimum). Increase Contrast set per §2.1. |
| A11Y-05 | Font scale to 200% with no clipping in card, sheet, toast; CMP-ACTIONCARD stacks at ≥ 1.6; everything else wraps. Casual and Linear both checked at 200%. Only Home header icons cap scaling (`maxFontSizeMultiplier` 1.5). |
| A11Y-06 | Toast/snackbar is announced, lasts 8 s, pauses while touched or focused; Undo also on Home (Added) and in History. |
| A11Y-07 | Confirm sheet traps focus, starts on the first blocking flag, restores focus on close; pickers work with VoiceOver/TalkBack. |
| A11Y-08 | Reduced motion: cross-fades only (§3); no flashing content. |
| A11Y-09 | Errors are text, attached to their field, announced (`accessibilityLiveRegion` polite / `announceForAccessibility`). |
| A11Y-10 | Thumbnails have text: "Screenshot, Nov 18, Pizza Night flyer, Draft". The screenshot in the sheet has a label from title/class. |
| A11Y-11 | Targets ≥ 44 × 44 pt iOS / 48 × 48 dp Android. Supports Bold Text and dark mode. |

Pre-explainers follow https://developer.apple.com/design/human-interface-guidelines/privacy.

---

## 7. Implementation guidance

### 7.1 Libraries (Expo / React Native)
Expo Router (native stack; `presentation: 'formSheet'` + `sheetAllowedDetents`, verify option names on the pinned SDK), `react-native-reanimated` (ink-in, layout animations, `useReducedMotion`), `react-native-gesture-handler` (swipe rows), `@shopify/flash-list` v2 (fallback v1 / FlatList), `expo-image` (thumbnails from pre-generated files), `@react-native-community/datetimepicker`, `expo-haptics`, `expo-symbols` + `@expo/vector-icons` (verify Material Symbols Rounded availability; else ship the icon font), `expo-font` + `@expo-google-fonts/recursive` (verify Casual statics), `expo-notifications` (Android channels and action categories), `expo-share-intent` (iOS share extension config plugin), `expo-media-library` (catch-up), `expo-image-picker` (`selectionLimit: 20`), `react-native-safe-area-context`. No UI kit, no Storybook, no Style Dictionary.

### 7.2 One `theme.ts`
```ts
// src/theme.ts — the only source of tokens; components never use raw hex
export const palette = {
  light: { desk:'#E8EBEE', sheet:'#FFFFFF', sheetRaised:'#FFFFFF', sunken:'#DDE1E6',
    graphite:'#2A2E35', graphiteSoft:'#5A616B', hairline:'#CDD3D9', ink:'#22398F',
    onInk:'#FFFFFF', inkFlood:'rgba(34,57,143,0.14)', highlighter:'#FFE36E',
    onHighlighter:'#2A2E35', correction:'#B3261E', toastBg:'#2A2E35', toastText:'#FFFFFF' },
  dark: { desk:'#14171B', sheet:'#1D2126', sheetRaised:'#262B31', sunken:'#101316',
    graphite:'#E4E7EB', graphiteSoft:'#A3AAB4', hairline:'#343A42', ink:'#9EB3FF',
    onInk:'#14171B', inkFlood:'rgba(158,179,255,0.18)', highlighter:'#5A4A0C',
    onHighlighter:'#FFE36E', correction:'#F2B8B5', toastBg:'#E4E7EB', toastText:'#14171B' },
} as const;
export const space = { 1:4, 2:8, 3:12, 4:16, 5:20, 6:24, 8:32, 10:40 } as const;
export const radius = { sheet:28, card:16, button:12, field:10, thumb:6, mark:3, chip:999 } as const;
export const border = { width:1.5, widthHC:2 } as const;
export const type = { /* §2.2 tokens: family, size, lineHeight, weight, fontVariant */ };
export const motion = { check:120, flood:260, dry:300, fade:150, spring:{damping:18, stiffness:220} } as const;
export const contrastPairs = [ /* [fg, bg, min] for §7.5 */ ] as const;
export function useTheme() { /* useColorScheme() + Increase Contrast overrides */ }
```

### 7.3 `/states` dev route (plain; dev builds only)
One scrolling page, hard-coded props, rendered in light, dark and 200% text (toggle at top): CMP-ACTIONCARD in Draft-Ready, Draft-Ask, multi-action, Added, Undone, write-failed, sample; CMP-FIELDROW in normal, blocking, blocking-with-question, assumption, missing, anchor; CMP-THUMB in each status; CMP-BANNER in every variant used by ST-*; CMP-EMPTY variants; CMP-TOAST (Added, Removed, write-only). Ink-in has a "play" button and a reduced-motion toggle.

### 7.4 Three Maestro flows
Screenshots in light, dark and 200% text, reviewed by eye (no pixel diffs).
1. **MAE-MAGIC:** import the bundled sample flyer (stands in for share; Android also opens the NTF-CHECK deep link). Fixture: the flyer reads "Pizza Night, Thu Jan 22, 7, Student Center" plus "RSVP by Wed Jan 20", so the resolver returns a **blocking weekday/date conflict** on the date and a non-blocking "7 PM assumed" caption (D20). Steps: card [Review] → Confirm → assert "Check date to continue" → Looks right → Add → assert toast text and Added row.
2. **MAE-PERM-DENIED:** assert no permission prompt appears before ONB-2; deny Photos → assert ST-PERM-PHOTOS-DENIED banner; deny Calendar at Add → assert ST-PERM-CAL-DENIED and the Draft kept.
3. **MAE-UNDO:** Add → toast Undo → assert card back to Draft; Add again → search "pizza" → assert the tile → open read-only view → back → Home › Added → swipe Undo → assert "Removed from Personal" → Settings › History shows "Undone".

### 7.5 Contrast unit test
About 20 lines in Jest: compute WCAG relative luminance for each `contrastPairs` entry in both palettes and the Increase Contrast overrides, flatten alpha over its background, assert ≥ the stated minimum (4.5 text, 3 non-text). Pairs at minimum: graphite/graphiteSoft on desk, sheet, sunken; ink on sheet and desk; onInk on ink; onHighlighter on highlighter; correction on sheet; toastText and inverse ink on toastBg.

### 7.6 Review checklist (per PR touching UI)
- Tokens only (no raw hex); vocabulary table followed.
- Every ST-* for the screen renders in `/states` or a Maestro flow.
- VoiceOver + TalkBack, reduced motion, dark mode and 200% passes.
- Android Back works on any sheet.
- 10k-item fling ≥ 55 fps; tap-to-write-started ≤ 500 ms; ink-in ≤ 700 ms.

### 7.7 Cut order (if the build slips)
0. Increase Contrast set (first token cut, D21; skipped anyway if React Native exposes no setting). 1. (Retired: notifications already carry [Review] only, D19; nothing to cut. Number kept.) 2. Long-press source quote on CMP-FIELDROW. 3. Calendar color dot (keep name). 4. Ink-in flood: fall back to the 150 ms cross-fade (keep the font and border swap). 5. Recursive fonts: fall back to system font (keep dashed vs solid). 6. Search (the last planner cut, BUILD_HANDOFF §8 item 12), keeping the Added and Not sure chips.
**Never cut:** Draft/Added distinction, blocking flags and the "Check … to continue" button, Undo (toast + Added filter + History), honest error/empty/offline/permission/sensitive states, the data-flow page, dark mode, 200% text.

### 7.8 Reconciliation table

| # | Older source said | Final | Authority |
|---|---|---|---|
| 1 | "Quiet paper + one ink", stock indigo/amber/green/teal, dark #0B0B0D; success = green, private = teal | "Pencil, highlighter, ink"; Ink + Highlighter + Correction; dark Desk #14171B; Added = Ink + check; Kept on this phone = Graphite + lock | D12 |
| 2 | `type.mono` for dates | Recursive Linear tabular for dates/values | D12 |
| 3 | Dates in Recursive Casual while Draft (brainstorm) | Casual on title only, Draft only | D12, Impeccable P1 |
| 4 | Card radius 20, pill buttons, card shadow | card 16, button 12, thumb 6, no card shadow | D12 |
| 5 | 9 screens + tab bar (Search, Detail, History, Privacy, Gallery) | 4 screens, no tab bar; Detail = read-only Confirm | D11 |
| 6 | History only in Settings (rebuttal) | plus Added filter and swipe-undo on Home | D13 |
| 7 | Add disabled until flags resolved | stays active; "Check … to continue" (e.g. "Check date to continue") scrolls to flag | D13, D20 |
| 8 | Inferred year was a blocking amber flag | non-blocking assumption caption; anchor caption | FEATURES F3 R4 |
| 9 | Toast 6 s (2_ui), 10 s (2_actions) | 8 s, pause on touch/focus | D13 |
| 10 | "Toast" everywhere | snackbar naming on Android | D13 |
| 11 | 4 ONB pages, looping demo, ONB-3 did 3 jobs | still image; one decision per screen; iOS coaching step | D13, rebuttal |
| 12 | ONB-2 "Nothing is saved on the server" | verified retention (D3) + names in chats are sent; no "not stored" claim | FEATURES F7 R4 |
| 13 | Notifications asked after first proposal (both) | Android: right after Photos, own screen; iOS: none in beta | FEATURES R4, D13 |
| 14 | iOS write-only calendar "less scary" | full access by default; write-only = no undo | D7 |
| 15 | Reminders, ladder chips, ACT-REM/ACT-LAD, morning-of 08:00 | one calendar item, ≤ 3 alerts (18:00 day before, 09:00 morning of, custom); no Reminders permission | FEATURES F5 merged |
| 16 | iOS Notification Content Extension rich card; App Intent/Back Tap | cut; iOS = share extension + catch-up | D10 |
| 17 | Notification [Add] only with 0 flags | NTF-READY has [Review] only (D19 overrides the earlier [Add]); Ask = "N things to check" [Review] only; Needs a look no push | D17, D19 |
| 18 | Ask push shows the question (5_ai) | push says "N things to check"; the question lives in the field row | D17 |
| 19 | Resurfacing nudges, cold-start nudge, 20% randomisation (5_ai) | no resurfacing pushes; shadow log only | D15 |
| 20 | 2% "Is this right?" audit | not in beta | D14 |
| 21 | "Not sure" card for hard cases (D2) | = ST-GATE-NEEDSLOOK: Library badge only, no push | F2f, D17 |
| 22 | "Send anyway" on sensitive | removed | FEATURES F7 R4 |
| 23 | Sensitive-guard toggle in Privacy (2_ui) | removed: F7b is non-negotiable | FEATURES F7(b) |
| 24 | Image upload opt-in, default off (D2) | default on for shared/imported (not sensitive/chat); opt-in for auto-detected | FEATURES F7 R4 |
| 25 | Semantic search, "Related" label, offline meaning caption | FTS5 only; none of these | FEATURES F6 R4 |
| 26 | Fly-in stagger, amber wipe, ⚠→✓ morph, pulse ring | cut | rebuttal |
| 27 | Confirm morph ≤ 500 ms; motion ≤ 500 ms; QA-PERF-04 tap→toast ≤ 500 ms | ink-in ≈ 680 ms (≤ 700); segments ≤ 350; QA-PERF-04 split: write-started ≤ 500 ms, animation ≤ 700 ms | D12 |
| 28 | Style Dictionary, Theme.swift, Storybook, SCR-GALLERY, swift-snapshot | one theme.ts, `/states` route | D11 |
| 29 | QA-SNAP pixel diffs 0.1%, Detox/Storybook, detail view | 3 Maestro flows, eye-reviewed screenshots; QA-SNAP state lists map to `/states` + flows; "detail" = read-only Confirm, "history list" = Settings › History | D11, D13 |
| 30 | QA-A11Y-01 "Proposed event" label | "Draft event" | D13 |
| 31 | `@gorhom/bottom-sheet` | native formSheet preferred | D13 |
| 32 | Dynamic Color unspecified | static scheme | D13 |
| 33 | AX5 reflow everywhere | only ACTIONCARD stacks at ≥ 1.6; 200% is the bar | rebuttal |
| 34 | Proposal / Proposed / Discard proposal | Draft / Ready to add / Dismiss | D13 |
| 35 | Thumbnail 9:19.5 crop | cover-crop any aspect, pre-generated thumbs | D13 |
| 36 | "No multi-select" vs "imports capped at 20" | no in-app multi-select; system picker with limit 20 | FEATURES F1(e) |
| 37 | First catch-up treats whole library as new | install watermark; never pre-install screenshots | FEATURES F1(e) |
| 38 | Delete copy "incl. server copies" | "Deletes from this phone" unless the server stores something | rebuttal, FEATURES F7 R4 |
| 39 | Empty-state line illustration | system icon | rebuttal |
| 40 | Ready card [Add …] writes from the card | Ready card [Review] only; Add only in the sheet; Review then Add = 2 taps | D20 |
| 41 | Demo flag "Flyer says '7'. PM?" (blocking) | weekday/date conflict is the demo flag; missing AM/PM is an assumption caption | D20, DESIGN C7 |
| 42 | ST-CATCHUP "[Read them]" tap | automatic on open; banner informs only | D20 |
| 43 | "Default alerts" on all items; event wireframes with 2 alerts | "Deadline alerts"; events start with none | D20, DESIGN Q3 |
| 44 | Past date: blocking row vs "Past: no action" vs "already happened" | one rule: blocking date row, no push, no override | D20 |
| 45 | Notification-added confirmation with Undo | removed; not built (D19) | D19 |
| 46 | Calendar-denied [Open in Calendar] logged as "Added (can't undo from here)" | logged as "Sent to Calendar", no Undo (the app cannot know the user saved it) | D22.6 |

### 7.9 Purchases extension (added: purchases extension; D24)

**Beta: NO new screens, components, states or tokens ship (added: purchases extension).** A guard-passing receipt that shows a printed "Return by ‹date›" is an ordinary deadline and uses the existing CMP-ACTIONCARD deadline variant, the existing SCR-CONFIRM sheet and the existing field rows, flags, past-date rule and ST-SENSITIVE for guard blocks. Nothing is added to the component library, `/states`, the Stable ID index or the contrast test. The title and date come from the screenshot like any deadline; no return-policy wording is added anywhere.

**Post-beta (not built, not sized; only after the F8 promotion trigger: receipts ≥15% of processed screenshots AND ≥30% showing a printed return date) (added: purchases extension).** The purchase card is a **CMP-ACTIONCARD variant** (planned ID CMP-ACTIONCARD-PURCHASE, defined when built), using existing tokens only (Ink, graphite, Highlighter mark, Correction, `cardTitleDraft`, `fieldValue`, `caption`; no new color, radius or type style). Layout: the usual thumbnail, state label, title "‹Retailer› order", one date line, up to 2 field lines (items, total), then the rule line "Policy: ‹N› days from ‹delivery/order›, checked ‹last_verified month›, source ‹link›", and [Dismiss] / [Review]. Deadline states, shown with the existing CMP-BADGE and date-line styling:

| State | Condition | Treatment |
|---|---|---|
| Open | more than 7 days left | normal date line "Return by ‹date›" |
| Closing soon | 7 days or fewer left | date line in Correction color plus a "Closing soon" badge; the shape, not color alone, carries it (A11Y-consistent with ST-PAST) |
| Passed | date is past | existing "Past date" treatment (ST-PAST rule: blocking date row, no push, no override) |

**Unknown retailer** is a blocking field row (existing CMP-FIELDROW blocking variant, Highlighter mark), with the one-line question: **"Unknown retailer: when does your return window end?"** The user types or picks a date; the app never fills a guessed date. A stale policy row (older than its review window) shows an assumption line "Policy not re-checked recently" and requires [Looks right] before Add. Warranty (slice 2) reuses the same variant with "Warranty ends" and the same three states. All fields remain editable, and Add still writes to the calendar only after the confirm tap.

---

## 8. Stable ID index

**Screens:** SCR-ONBOARD (ONB-1 Value, ONB-2 Data flow, ONB-3 Try it, ONB-4 Photos, ONB-5 Notifications [Android], ONB-6 Share-sheet coaching [iOS]), SCR-HOME, SCR-CONFIRM (incl. read-only view), SCR-SETTINGS (Capture, Calendar, Privacy, History, Delete all).

**Components:** CMP-THUMB, CMP-ACTIONCARD, CMP-FIELDROW, CMP-CHIP, CMP-SHEET, CMP-BTN, CMP-INKIN, CMP-TOAST, CMP-BANNER, CMP-BADGE, CMP-ROW, CMP-GRID, CMP-SEARCH, CMP-SKELETON, CMP-EMPTY, CMP-DATAFLOW, CMP-COACH, CMP-NOTIF (NTF-READY, NTF-CHECK), CMP-DIALOG.

**States:**
- Gating: ST-GATE-READY, ST-GATE-ASK, ST-GATE-NEEDSLOOK.
- Field: ST-BLOCKING, ST-ASSUMPTION, ST-PAST, ST-RESOLVE-FAIL.
- Capture/library: ST-EMPTY-NEW, ST-LOADING, ST-READING, ST-SLOW, ST-CATCHUP, ST-IMPORT-CAP, ST-DUPLICATE, ST-NOTHING, ST-SENSITIVE, ST-OFFLINE, ST-SERVER-ERR, ST-BASIC, ST-PAUSED, ST-UPGRADE, ST-RESTORED-MISSING, ST-AUTODETECT-FALLBACK, ST-SEARCH-NONE, ST-SEARCH-EMPTY-QUERY, ST-ADDED-EMPTY.
- Permissions: ST-PERM-PHOTOS-DENIED, ST-PERM-PHOTOS-LIMITED (iOS + Android 14), ST-PERM-NOTIF-OFF, ST-PERM-CAL-PREASK, ST-PERM-CAL-DENIED, ST-CAL-WRITEONLY.
- Actions: ST-ADDED, ST-UNDONE, ST-ALREADY-ADDED, ST-RECONCILE, ST-WRITE-FAILED, ST-NO-CALENDAR, ST-SYNC-PENDING, ST-UNDO-BLOCKED, ST-SAMPLE.
- Settings: ST-HISTORY-EMPTY (offline delete reuses ST-OFFLINE).

**Other:** A11Y-01…11, MAE-MAGIC, MAE-PERM-DENIED, MAE-UNDO, magic-moment frames A0–A7 and I0–I7. QA-PERF-01…05 and 07 (06 retired) and QA-A11Y are defined in DESIGN.md §8.5; this file references them.

**Tier summary.** Core: tokens §2.1–2.3, CMP-ACTIONCARD, CMP-FIELDROW, CMP-BTN primary, CMP-INKIN, CMP-TOAST, CMP-THUMB, CMP-SHEET, CMP-DATAFLOW (ONB-2), SCR-CONFIRM, Added filter/swipe-undo, ST-READING card, ST-WRITE-FAILED. Everything else is plain.
