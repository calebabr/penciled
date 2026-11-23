# 1b. Feature Prioritization (Feature Prioritizer)

Inputs: 1a_competitors.md, 1a_behavior.md, 1a_ideas.md. Date 2026-11-18; beta target mid-January 2027, which is about 8 weeks including the holidays.

## Confidence limits (read first)

- **User value scores rest on thin evidence.** The only category counts come from n=55 (S1). The 31% "offload memory" figure (S3) is secondhand. Messages/chats are probably undercounted. Events rank #1 by my estimate even though S1 never measured them. Treat user value as ±1.
- **Differentiation scores assume the competitor scan was complete.** "Nobody ships receipt-to-expense or recipe-to-grocery" is an absence-of-evidence finding from limited search. No Reddit or Play Store text was available.
- **Reliability scores are my judgment.** Nobody has measured extraction accuracy on real messy screenshots. The beta should collect that number.
- **Build cost assumes no native mobile work.** The dev has no native mobile experience. Anything that needs background photo-library access, OS calendar APIs or a real share extension costs much more than it does in the ideator's framing. I have scored it that way.

## Scoring

Scale is 1-5. **V** = user value; **D** = differentiation; **R** = reliability on messy real screenshots (for non-extraction features, how dependably the feature works in the field); **C** = build cost by mid-Jan (5 = cheap). Total is unweighted. In practice I weighted V and C highest because the deadline is fixed.

| # | Feature | V | D | R | C | Total | Note |
|---|---|---|---|---|---|---|---|
| 5 | Classify + extract with confidence flags | 5 | 3 | 3 | 4 | 15 | Core engine. Confidence flags are the cheap part |
| 6 | Context-aware date resolution (deterministic) | 4 | 3 | 5 | 4 | 16 | Pure Python date logic plus the screenshot timestamp. Very testable |
| 9a | Action cards: calendar + reminder | 5 | 2 | 4 | 3 | 14 | Highest-follow-up category. Apple ships calendar, but only on iPhone 15 Pro+ |
| 9b | Action cards: expense, grocery, saved link | 3 | 4 | 3 | 3 | 13 | Each adds a schema, a validator and a destination |
| 17a | Editable proposal (fields only) | 5 | 2 | 5 | 4 | 16 | Required by the confirm-every-action principle and complaint 9 |
| 17b | Source-region highlighting | 3 | 5 | 2 | 2 | 12 | Vision LLM bounding boxes are unreliable. Needs an OCR pass plus text matching |
| 7 | Multi-intent (event + its deadline) | 4 | 4 | 3 | 4 | 15 | Nearly free if the schema returns a list of actions |
| 11 | Deadline ladders (rule-based lead times) | 4 | 4 | 5 | 4 | 17 | Deterministic. Turns one reminder into real follow-through |
| 8 | Junk / "nothing to do" detection (basic) | 3 | 2 | 4 | 5 | 14 | Just an "other" class with a graceful empty state |
| 18 | Undo + action log | 4 | 3 | 4 | 3 | 14 | Undo means deleting through the calendar API, so it needs an API destination, not .ics |
| 19 | Privacy indicator + sensitive-content guard | 4 | 4 | 3 | 3 | 14 | Beta is cloud-processed, so it must be honest disclosure, not "on-device" |
| 2 | Share-sheet / upload entry | 4 | 2 | 4 | 3 | 13 | Android PWA share target and iOS Shortcut are cheap. A native iOS share extension is not |
| 1 | Auto-watch new screenshots | 5 | 3 | 3 | 1 | 12 | Needs a native app with background library access. Not feasible without native experience |
| 3 | Backlog sweep + graveyard report | 4 | 4 | 3 | 1 | 12 | Needs library access. LLM cost on hundreds of images. Pixel's caps are a complaint |
| 4 | Burst / scroll stitching | 3 | 4 | 2 | 2 | 11 | Merging across images is error-prone |
| 10 | Smart grocery merge | 3 | 4 | 2 | 2 | 11 | Unit normalization is a rabbit hole |
| 12 | Expense export (CSV) | 3 | 4 | 3 | 4 | 14 | Cheap once receipts are extracted |
| 13 | Search by meaning | 3 | 2 | 3 | 3 | 11 | Pixel has it. Search is retrieval, which the evidence says is the weaker job |
| 14 | Auto-collections | 3 | 3 | 2 | 2 | 10 | Clustering quality is hard to make feel smart |
| 15 | Timely resurfacing | 4 | 4 | 2 | 1 | 11 | Needs push plus context signals. Proactive features flop in the field (complaint 5) |
| 16 | "Still want this?" decay review | 3 | 3 | 4 | 2 | 12 | Deleting originals needs library write access |
| 20 | Teach-by-correction (explicit rules) | 3 | 3 | 4 | 3 | 13 | Needs edit history before it pays off |

## (1) Beta feature set: one magic moment

**Magic moment:** *"I screenshotted a flyer or group-chat message, shared it, and seconds later got a filled-in calendar event plus its RSVP or ticket deadline. I fixed the one highlighted field and tapped Add."*

Why this moment:

- **Strongest evidence.** Events and deadlines rank #1 on follow-up probability (behavior file). Calendar and reminder are also the one action type users already expect from these tools.
- **Most deterministic to validate.** Dates, times and places can be checked in code.
- **Measurable.** "Event added, unedited" is a clean success metric.
- **Fits testers who are likely students.** School and club flyers, syllabus deadlines and group-chat plans are the natural inputs.

The differentiation is not "calendar from screenshot," which Apple already ships. It is three things together:

- It works on any phone, including Android and older iPhones.
- It catches the secondary deadline in the same screenshot.
- It is honest about which field it is unsure of.

**Beta scope (8 items):**

1. **Share/upload entry (#2, minimal).** This is a React PWA, not a native app:
   - Android: Web Share Target.
   - iOS: an iOS Shortcut in the share sheet that posts the image to the backend and opens the confirm page, plus paste/upload as a fallback.
   - Architecture needs to verify this. It is the biggest unknown in the beta.
2. **Classify + extract with confidence flags (#5),** limited to three types: *event*, *deadline/to-do*, *nothing to do*. The model returns structured tool calls, Pydantic validates them, and failed validation produces a flagged field, never a guess.
3. **Deterministic date resolution (#6).** Relative dates ("tmrw 7", "this Fri") are resolved against the screenshot's capture time when EXIF/filename provides it, with a "today" fallback that is flagged. Year inference is also flagged.
4. **Multi-intent (#7),** capped at 3 actions per screenshot.
5. **Calendar event + reminder cards (#9a)** that write to Google Calendar through OAuth, with .ics download as a fallback for Apple/Outlook users. Reminders become timed calendar entries or tasks. No native Reminders app in beta.
6. **Deadline ladders (#11).** Three fixed rule presets, shown and editable on the card.
7. **Editable proposal (#17a)** with uncertain fields visually flagged, plus **undo + action log (#18)** for API-written items: a 10-second snackbar and a history list.
8. **Privacy disclosure + basic sensitive guard (#19, lite).** A plain statement that images go to a cloud model and are not retained after processing (retention policy to be decided by architecture). A pre-check refuses obvious banking, ID and password screens before any action is proposed.

Also include instrumentation: per-field edit rate, confirm rate and "nothing to do" rate. This is the extraction-reliability data the research lacks, and it validates the category ranking.

Explicitly **not** in beta: auto-watch, backlog, search, any action type other than calendar and reminder. If the share-entry path is working by about Dec 20 and time remains, the first stretch item is **expense export (#12)**, because it reuses the extraction pipeline.

## (2) Next 5 after beta (in order)

1. **Receipt → expense card + CSV export (#9b expense, #12).** Second-strongest category by evidence (S1 22/55). No competitor ships it as far as we found. Reuses the pipeline.
2. **Source-region highlighting (#17b).** The biggest trust differentiator. Do it after beta logs show which fields users distrust. Needs an OCR layer with boxes.
3. **Teach-by-correction (#20).** Only worth building once beta edit logs exist. Start with default calendar and merchant→category rules.
4. **Native capture: real share extension, then auto-watch (#2 full, #1).** The largest value jump and the largest cost. It probably means Expo/React Native. Do it only if beta testers say sharing is too much friction.
5. **Recipe → grocery list, simple append (#9b grocery, without #10 merge).** High commonness, intent to cook. Skip quantity merging until there is demand.

## (3) Rejected for now

- **#3 Backlog sweep + graveyard report:** needs native library access and costs LLM spend at scale. Revisit after #1 exists.
- **#4 Burst stitching:** low reliability. Merge errors across images undermine trust in the core loop.
- **#10 Smart grocery merge:** unit normalization is a time sink for a moderate-value feature. Plain append covers 80% of the need.
- **#13 Search by meaning:** retrieval is the job the evidence says users fail at less urgently. Pixel already does it. It pulls focus from actions.
- **#14 Auto-collections:** clustering often feels dumb at low data volume. Not a one-tap action.
- **#15 Timely resurfacing:** needs push and context signals. Field evidence shows proactive features are rarely noticed (Magic Cue, Now Brief).
- **#16 Decay review:** depends on library write access. A cleanup app is a different, crowded product (ShotSweep, ScreenSift).
- **#8 Learned personal-noise patterns (the "magic" half of #8):** basic "nothing to do" detection is in beta. Learning personal patterns is not needed at beta volume.
- **On-device processing as a promise:** not feasible for this builder by January. Claiming it would repeat complaint #1, a silent privacy mismatch. Disclose cloud processing honestly instead.

## Risks this prioritization depends on

- **Capture friction.** If the share-sheet path is clunky (the iOS Shortcut especially), the magic moment never happens. Prototype it in week 1, before any extraction work.
- **Calendar destination.** Testers who don't use Google Calendar get the .ics fallback, which can't support undo. Test this with recruited testers early.
- **Event density.** If testers rarely screenshot events (unvalidated, since S1 didn't measure it), the beta under-tests the core loop. Recruit testers from student orgs where flyers and schedules are common.
