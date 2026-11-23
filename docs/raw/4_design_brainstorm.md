# 4: Design brainstorm (visual identity, design only)

Method: frontend-design skill process. I drafted a plan, checked it against the brief and the skill's list of AI-default tells, then revised it. Scope respects 4_rebuttal_ui.md: 4 screens, one `theme.ts`, no Style Dictionary or Storybook, and the must-be-beautiful core only.

## 1. Critique of 2_ui.md "quiet paper + one ink"

**Generic (defaults, not choices):**
- **The palette is stock Tailwind.** `#4F46E5` is indigo-600, `#B45309` is amber-700, and `#15803D` is green-700. An indigo accent on off-white is the default SaaS look, and nothing in it says "calendar" or "screenshot".
- **The dark canvas `#0B0B0D`** is the tinted near-black tell (skill trait 5).
- **System font everywhere, plus `type.mono` for dates.** Monospace for data is a listed tell, and system-only type leaves the personality at zero.
- **Template chrome in the wireframes:** "READY (2)" and "LIBRARY" in all caps, an eyebrow above the title ("Event · Proposed"), and middle-dot meta strings ("Fri Jan 22 · 7:00 PM", "Added to Calendar · 2 reminders set").
- **The SaaS card kit:** 20 pt radius, the same soft 6% shadow, and pill buttons.
- **Five semantic hues** (indigo, amber, green, red, teal) work against the "one ink" line in the same doc.

**Specific to this product (keep):**
- **"Draft until you tap."** The dashed-to-solid change is the core principle made visible. It is the best idea in the doc.
- **One clear flag with a reason**, plus the two flag tiers.
- **The screenshot is the hero**, with the source next to every field.
- **No sparkle, gradient or chat bubble.** This is the right call for a trust product.

**Diagnosis:** the *concept* (draft vs. confirmed) is specific, but the *skin* is generic. The metaphor needs to go one level deeper: plans are **pencilled in** and then **inked**. That is the plain-English idiom for tentative vs. committed calendar entries, and students live in pencil, highlighter and ink.

## 2. Revised identity: "Pencil, highlighter, ink"

### Color (6 named tokens)
| Name | Light | Dark | Role |
|---|---|---|---|
| Desk | #E8EBEE | #14171B | canvas (cool, not cream) |
| Sheet | #FFFFFF | #1D2126 | cards, sheet |
| Graphite | #2A2E35 | #E4E7EB | text; the **draft** dashed line (secondary text #5A616B / #A3AAB4) |
| Ink | #22398F | #9EB3FF | the only action color; **confirmed** state |
| Highlighter | #FFE36E (fill) | #5A4A0C fill, #FFE36E text | **blocking** flag only |
| Correction | #B3261E | #F2B8B5 | errors and delete only (not identity) |

- **Green "success" is cut.** Confirmed means Ink plus a check. Teal "private" is cut too: "Kept on this phone" becomes a Graphite badge with a lock icon. The result is two identity hues, Ink and Highlighter.
- **Contrast:** Graphite on Highlighter is about 11:1. Ink on Sheet is about 10:1. The Ink tint is used only as a transient flood (see Motion). Verify all pairs in the existing contrast test.

### Type
| Role | Font (expo-google-fonts) | Use |
|---|---|---|
| Draft title + values | **Recursive Sans Casual**, Semibold 600 | card title, date/time values while the item is a draft |
| Confirmed title + values | **Recursive Sans Linear**, Semibold 600 | the same text after confirm |
| Date line | Recursive Linear/Casual 600, 22/28, tabular figures | "Fri, Jan 22, 7 PM" |
| Chrome | system (SF Pro / Roboto) | labels, buttons, settings, search |

Recursive's Casual↔Linear axis is literally pencil→ink. One family appears only inside the card and the confirm sheet; everything else is native. Two static instances are about 150 KB total. *Verify* that `@expo-google-fonts/recursive` ships Casual statics; if not, instance them once with `fonttools varLib.instancer` and commit the two TTFs (one-time, S). Drop `type.mono`.

### Signature element: the ink-in
All the boldness is spent on the draft→confirmed transformation:

```
DRAFT (pencil)                      ADDED (ink)
┌ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┐         ┌─────────────────────────┐
  ▯  Pizza Night  (Casual)          │▯  Pizza Night  (Linear) │
  ▯  Fri, Jan 22, 7 PM              │▯  Fri, Jan 22, 7 PM   ✓ │
  ▯  ▐Year 2027▌ check this         │   Added to Personal     │
     Draft          [ Add 2 ]       └─────────────────────────┘
└ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┘          solid 1.5pt Ink border
 dashed 1.5pt Graphite border
```

On Add, Ink floods out from the button across the card. The pencil border becomes an ink rule, and the title re-sets from Casual to Linear under the flood. The tint then "dries" back to Sheet, leaving an ink border and a check.

### Shape
Radii encode hierarchy rather than using one value everywhere:
- sheet: 28 (system)
- card: 16
- buttons: 12 (not pills; they echo the card)
- thumbnail: 6 (reads as a photo of a screen)
- highlighter mark: 3
- chips: pill

There are **no card shadows**. State is carried by the border (dashed vs. solid), not by elevation. Dark mode uses Sheet over Desk.

### Motion: one orchestrated sequence
The sequence keeps the rebuttal's two steps:

1. The button label becomes ✓ (120 ms).
2. An Ink circle scales from the tap point, clipped by the card (260 ms, ease-out). The success haptic fires at flood *start*, the moment the ink "hits". The font swap and the border swap happen at 50%.
3. The tint dries to 0 while the card compacts (300 ms).

Total ≈ 680 ms. Under reduced motion, this becomes a 150 ms cross-fade. Build: one absolute `Animated.View` plus `withTiming`, which costs the same as the planned cross-fade (M).

### Self-review: what I revised and why
- **First draft used a warm notebook-cream canvas plus a serif title.** That is trait 1, so I switched to the cool Desk/Sheet canvas and a sans with a Casual axis.
- **First draft considered a corkboard/pinned-flyer card with a tape strip.** It was decorative and off-brief, so I cut it.
- **First draft had a calendar tear-off date block.** It is generic and competes with the thumbnail, so I cut it.

## 3. Delight ideas (cheap, magic-moment first)

1. **Pencil→ink type swap** (S; F2/F4). Two fonts and a conditional `fontFamily`. The draft *looks* tentative even in a still screenshot.
2. **Highlighter flags** (S; F2/F3). A blocking flag puts a Highlighter fill behind *the value text only*, not the whole row. "Looks right" fades it out. Non-blocking assumptions stay as Graphite captions ("Year: 2027, inferred").
3. **Undo un-inks** (S; F4c/F7). Undo plays the flood in reverse, and the card returns to a pencil draft instead of vanishing. This shows "removed from calendar, proposal kept". Toast: "Removed from Personal".
4. **The button says exactly what it writes** (S; F4b/F5): "Add event + 2 alerts", and the toast echoes "Added event + 2 alerts to Personal". The verb stays the same across button, toast and History.
5. **Destination color dot** (S; F4). Next to "Added to Personal", show the user's calendar's own color (from EventKit/CalendarContract) as an 8 pt dot. This confirms *where* it went without adding a palette hue.
6. **"Where did this come from?"** (S if the extraction schema returns a short source quote per field; F2/F7). Long-pressing a field shows the source quote, e.g. "from: 'Fri 7p @ Student Ctr'". This is a no-OCR-box stand-in for post-beta source-region highlighting.
7. **Grid status by shape** (S; F6). In the Library, drafts get a dashed Graphite outline and added items get a small solid Ink corner tick. Status reads at thumbnail scale without a text badge on every tile. Badges stay for accessibility labels.
8. **Skeleton rows in pencil** (S; F1 iOS ≤2 s). Loading field rows are dashed Graphite lines, so the wait already looks like the draft that is coming.

**Feature ideas from the design lens (all post-beta):**
- **"Pencil it in" option:** write the event as *tentative/free* in the calendar and ink it later.
- **Share the inked card** as an image back to the group chat ("Added. You?"). This is a student growth loop.
- **Weekly "ink or erase"** pass over stale drafts. This folds into queue item 4 (backlog sweep).

## 4. Exact edits for the Chair (UI.md)

1. **§1 visual direction:** rename it "Pencil, highlighter, ink". Principle 1 becomes "Pencilled in until you tap; inked when added."
2. **§2.1 tokens:**
   - Replace `bg.canvas` with Desk, `bg.surface` with Sheet, `text.primary` with Graphite, `accent` with Ink (#22398F / #9EB3FF), and `flag`/`flag.tint` with Highlighter (blocking only).
   - Delete `success` and `private`. Confirmed = Ink + ✓; private = Graphite + lock.
   - `danger` → Correction #B3261E / #F2B8B5.
   - Dark `accent.onAccent` → #14171B.
3. **§2.2 typography:**
   - Add `type.cardTitle` and `type.dateLine` (Recursive Casual for draft, Linear for confirmed, 600, tabular figures).
   - Delete `type.mono`.
   - Chrome stays system.
4. **§2.3 radii and elevation:**
   - card 16, button 12 (non-pill), thumbnail 6, highlighter 3.
   - Delete `elev.1` from cards.
   - Draft border: 1.5 pt dashed Graphite. Confirmed border: 1.5 pt solid Ink. Increase Contrast: 2 pt.
5. **§3 Confirm row:** replace it with the ink-in (check 120 → flood 260 + haptic at start → dry/compact 300). Amend the motion rule to "each segment ≤ 350 ms; one sequence ≤ 700 ms". Undo = reverse flood.
6. **Copy tells:**
   - Drop the all-caps section labels. Use "Ready to add" and "Library" in sentence case.
   - Drop "Event · Proposed" eyebrows. The state label is "Draft" / "Added".
   - Replace middle-dot meta strings with commas ("Fri, Jan 22, 7 PM").
   - The toast reads "Added event + 2 alerts to Personal [Undo]".
7. **`/states` route:** render each card in draft, blocking-flag, assumption, inked and un-inked states, in light, dark and 200% text.
