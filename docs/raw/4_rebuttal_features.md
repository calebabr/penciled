# 4 — Feature prioritizer rebuttal to red team

Scope: only the attacks that change FEATURES.md. Architecture, server, eval and store attacks (R8, R11, R12) are out of scope here; I endorse them.

**R1/R2: iOS capture. CONCEDE.** Cut the Back Tap/App Intent from F1(b).
- Revised F1(b): "Android: a new screenshot produces an 'action ready' notification without opening the app. iOS: share-sheet is the primary path; screenshots taken since the last open are caught up when the app opens. The UI says this plainly."
- Revised magic moment, one per platform: Android is "screenshot → notification ≤10 s"; iOS is "share → card ≤2 s (processing started), card filled ≤8 s".

**R3: headless Android pipeline. DEFEND the feature, add a gate.** Auto-detect stays the Android target. Add to F1: "If neither headless JS nor the thin Kotlin path works by end of week 2, Android drops to the iOS model (share + catch-up on open), and F1(c) messaging applies."

**R4a: images off by default. REVISE D2/F7.** "When the user shares or imports an image, it is sent as a downscaled image by default, unless the guard marks it sensitive or it is a message/chat screenshot (those send redacted text only). Auto-detected screenshots send text only unless the user opts in." Sharing is explicit intent, and the hero flyer case needs the image.

**R4b/R4c/R14/C7: dates. REVISE F3.**
- "Relative dates are anchored to an OCR'd day header in the screenshot ('Yesterday', 'Mon 3:12 PM') when one is present, otherwise to capture time (or import time). The anchor is shown on the card and can be changed with one tap."
- "**Blocking** flags apply only when a required field is absent or fails validation. **Assumptions** (inferred year, AM/PM inferred from context, the anchor) are shown in a distinct non-blocking style."
- Chat negotiation ("Sat?" / "no, Sun"): the last-mentioned date wins and is flagged blocking when more than one candidate exists.

**R4d: week-1 50-screenshot test. DEFEND** as a gate, not a feature: it decides whether R4a is enough.

**R5: permission wall and ladder. CONCEDE.** F5 becomes part of F4.
- Revised F4: "Both actions write **one calendar item**: an event, or a deadline (timed at the due time, all-day if no time is given). A deadline carries up to 3 alarms (presets: 1 day before at 18:00, morning-of at 09:00, plus one custom). Alarms are visible and editable, never in the past. One item, one Undo." This resolves C18.
- Delete F5 as a standalone feature. Cut Reminders, exact alarms, BOOT_COMPLETED and the local-notification fallback.
- Permission count: iOS asks for 2 (Photos, at catch-up; Calendar full, at first confirm with a pre-prompt per D7). There is no notification ask on iOS. Android asks for 3: Photos, then Notifications immediately after, then Calendar at first confirm. This fixes C21. C11 is resolved for D7: full access, write-only = degraded no-Undo.

**R6/R7/C19: search. REVISE F6, don't cut.** The library is the home screen, and dropping search loses retrieval entirely.
- Revised F6: "Library + text search. FTS5 over OCR text and extracted fields. p95 ≤300 ms on 10k seeded items. Feed scrolls smoothly at 10k seeded items."
- Embeddings/meaning search moves to the post-beta queue as #2.

**R10/C10/C12/C20: privacy. CONCEDE** "Send anyway" and source-app detection. F7(b) stands as written.
- Revised F7(a): "Onboarding states the provider's actual retention period (verified by the D3 spike) and that names in chat text are sent. It never says 'nothing is saved' unless that has been verified."
- Revised F7(d): "Delete removes all on-device data for one item or all items. Test: the server has no table holding screenshot content or extracted text."
- Disclose that the guard is English-only.

**R9/R13: backlog. CONCEDE.** Add F1(e): "Screenshots taken before install are never processed automatically. The user can import up to 20 at a time." Backlog sweep stays post-beta.

**F8: DEFEND** unchanged; it is counts only and cheap.

Net: 8 features become 7. F5 is merged into F4, and F6 is narrowed.
