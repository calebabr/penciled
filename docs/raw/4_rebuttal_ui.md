# 4 — UI/UX rebuttal to red team (design only)

## Responses

**R6 UI scope: CONCEDE, with one REVISE.** We ship 4 screens.
1. **SCR-ONBOARD**: 3 pages. ONB-1 is a still image (the looping demo is cut), ONB-2 shows the data flow, and ONB-3 combines Try-it with Photos, then Notifications.
2. **SCR-HOME**: Ready cards, then the Library grid, then a search field at the top of the grid. This absorbs SCR-SEARCH as a filter over FTS5 results, with scope chips and no "Related" label.
3. **SCR-CONFIRM**.
4. **SCR-SETTINGS**: absorbs SCR-PRIVACY, plus a History section that absorbs SCR-HISTORY.

SCR-DETAIL is cut as a screen. Tapping a thumbnail opens SCR-CONFIRM read-only for confirmed items (screenshot, fields, action line with [Undo], overflow Delete), so we reuse one sheet. The tab bar is cut. SCR-GALLERY is cut. *REVISE:* I keep **CMP-ACTIONCARD's draft-to-confirmed morph**, simplified (see Motion), because it is the only place the core principle becomes visible.

**R5 / C21 / C11: Permission wall: CONCEDE + REVISE.**
- **Android:** Notifications are asked immediately after Photos (ONB-3), because the first proposal *is* a notification.
- **iOS:** Notifications are deferred to after the first card (unchanged).
- **Calendar:** asked at the first [Add]. Full access on iOS per D7. The pre-explainer is one line: "Full access lets you undo." C11 is resolved in favour of D7.
- **Reminders:** the Reminders permission is dropped (adopting the calendar-alarm cut). CMP-CHIP ladder presets now label alarms ("Alert: day before"). Same chips, no new UI.

**R2: iOS magic moment: CONCEDE.** iOS F1–F2 frames become: share sheet, then an in-app SCR-CONFIRM, with the target of 2 s or less covered by CMP-SKELETON field rows. The Notification Content Extension is cut (C1). Android keeps BigPicture + [Review]. ONB copy on iOS says "Share a screenshot to us" plainly.

**R4(c) / C7: Flags: REVISE.** There are two tiers:
- **Blocking**: a validation failure, AM/PM missing, or a date in the past. Uses `flag.tint`, and Add is disabled.
- **Shown assumption**: an inferred year, or an anchor date. Shown as an inline grey caption with an info icon ("Year: 2027, inferred"), tappable, and non-blocking.

This keeps "one clear flag beats five weak ones" honest.

**R14: REVISE.** The anchor is a non-blocking caption on SCR-CONFIRM: "Relative to Tue Nov 18 ▾". One tap opens the date picker.

**R10 / C12 / C20: CONCEDE.** ONB-2 copy states the verified retention period from D3 and "names in chats are sent." There is no "not stored" claim until D3 is verified. The "Send anyway" control is removed from ST-SENSITIVE. The per-item delete copy is "Deletes from this phone" unless the server stores something.

**R13: CONCEDE.** There is no multi-select UI in the beta.

**Motion: REVISE.**

*Keep (Reanimated layout + `withSpring`):*
- the Confirm sequence, simplified to two steps: the button becomes a check, then the card cross-fades from draft to solid and compacts
- the card's arrival
- the toast rising
- the flag fading to neutral on "Looks right"
- 4 haptics

*Cut:*
- the field fly-in stagger
- the amber wipe
- the ⚠→✓ morph (now an icon swap)
- the processing pulse ring (now a static "Reading…" badge)

Reduced motion uses cross-fades only (unchanged).

**C17 Toast: REVISE.** The undo toast lasts **8 s**, paused while touched or focused. This reconciles with QA-A11Y-06.

**Token tooling: CONCEDE.** Style Dictionary and Theme.swift are cut. The new setup is **one `theme.ts`** with semantic light/dark tokens exactly as in §2.1–2.3, plus `useTheme()`. The contrast unit test stays (about 20 lines over the token pairs) because it is cheap.

**Gallery / snapshot: CONCEDE + REVISE.** Storybook, the pixel diffs, and the swift-snapshot suite are cut. What remains:
- **3 Maestro flows**: the magic moment, permission denied, and undo. Each takes screenshots in light, dark and 200% text that are reviewed by eye, not diffed.
- A **dev-only route `/states`**: one scrolling page that renders CMP-ACTIONCARD, CMP-FIELDROW, CMP-BANNER and CMP-EMPTY in every state, with hard-coded props. It replaces SCR-GALLERY at about 1/10th the cost.

**AX5 reflow: REVISE.** Only CMP-ACTIONCARD stacks vertically at a font scale of 1.6 or more. Everything else wraps naturally. The 200% smoke test is the bar (adopting R6).

**R7 FlashList v2: DEFEND conditionally.** The Library grid needs virtualization. If the SDK pin fails, fall back to FlashList v1 or FlatList with `getItemLayout`. There is no visual change.

## Must-be-beautiful core

These get polish, motion, dark mode and an a11y pass:
- CMP-ACTIONCARD (draft vs. confirmed)
- SCR-CONFIRM
- CMP-FIELDROW (both flag tiers)
- CMP-BTN primary with the confirm morph
- CMP-TOAST with Undo
- CMP-THUMB
- ONB-2 data-flow page
- Color, type and radii tokens (§2.1–2.3)

## Ship plain

These use system defaults, no custom motion, and tokens for color only:
- SCR-SETTINGS (incl. Privacy and History rows, using CMP-ROW)
- CMP-SEARCH + scope chips
- CMP-BANNER (all ST-* states)
- CMP-EMPTY (an SF Symbol or Material icon instead of an illustration)
- CMP-SKELETON (static)
- CMP-BADGE
- CMP-CHIP
- ONB-1 and ONB-3
- the `/states` dev route

**Never cut:** the draft/confirmed distinction, blocking flags, undo, honest error/empty/offline states, dark mode, and 200% text.
