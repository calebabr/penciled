# 4 — Rebuttal: AI pipeline designer (Round 4, design only)

Verdicts on red-team attacks that touch the AI pipeline. Every number is an estimate *(est.)* until the week-1 test measures it.

## 1. Where AI-RESOLVE runs (R3, C5): REVISE
There is **one resolver, in Python, on the server**, whichever way the Android trigger runs: headless JS, or the thin Kotlin path of OCR → guard/redact from a shared JSON regex ruleset → POST. The server runs GROUND → RESOLVE → VALIDATE → CONF → PROPOSE and returns the card JSON plus the notification text. The device keeps the regex-only AI-GATE and does no date maths. Two consequences:
- `local_only` items get a manual card with no pre-filled dates.
- When the API is down, the "basic" card shows the title and the dated OCR line with all fields `needs_review`. It shows no resolved datetime.

The AI §4 schema (labels, `RawWhen`, 5 classes) is canonical (C6).

## 2. Text-only vs image for share/import (R4a, C8): REVISE (chair must amend D2)
- **Share/import (user-initiated):** an image is sent **only when an AI-ESCALATE trigger fires**, not on every share. This is on by default and disclosed at onboarding ("hard images may be sent once to read them"), with a Settings switch to turn it off.
- **Auto-detect:** stays opt-in.
- **Sensitive and `local_only` items:** never sent in either case.
- **Image size:** one value, long edge 1,568 px with the status bar cropped.
- **Week-1 rule:** if the text-only path leaves more than 25% of stylised flyers as "Not sure" or wrong, this revision is final. If it is under 10%, D2 stands unchanged.

## 3. Chat date anchoring (R4b, R14): REVISE
- **Detecting a chat:** 3 or more OCR lines match bubble or timestamp patterns, or the model's `source_hint` is "chat".
- **Per-line anchor:** day headers ("Today", "Yesterday", "Mon", "Nov 14", "Mon 3:12 PM") are parsed in OCR order. Each line inherits the nearest header above it, resolved back from the capture date. The model already returns `evidence.line`, so RESOLVE uses that line's anchor.
- **No header above the evidence line:** a relative word ("tmrw", "Sat") is resolved against the capture time and flagged `needs_review` ("relative to when you took the screenshot"). Absolute dates are not flagged.
- **Negotiations:** a new prompt rule says the latest date or time in OCR order that is proposed or accepted wins. If two dates conflict and neither is clearly accepted, the date field is `needs_review` and `notes_for_user` reads "Sat or Sun? Pick one". Sender identity is not needed for this.
- **Anchor display:** every relative resolution shows "relative to Tue Nov 18". One tap changes it, which covers imported and forwarded images.

## 4. Inferred year (R4c, C7): DEFEND + REVISE
AI §6 already makes `assumed` non-blocking; the attack is aimed at the UI's rule that every flag blocks. Revision:
- A year chosen by the grace rule shows **no chip**; the year is simply printed in the date.
- An `assumed` chip appears only for a year rollover or a date more than 6 months away.
- Missing AM/PM is `assumed` (non-blocking). The one exception is "12am", which stays `needs_review`.
- Only `needs_review` disables Confirm.

## 5. Cost and backlog (R9, R13, C23): CONCEDE
- An install-time watermark: catch-up only considers screenshots taken after install.
- No backlog import, no Batch API and no AI-BACKLOG stage in the beta. Multi-select import is capped at 20.
- No Sonnet. If a Haiku vision call fails, the result is a "Not sure" card.
- A $25/month provider cap, a stable idempotency key, and a retry budget of 3.
- **Beta estimate:** 50 testers × 20 screenshots/day × 50% passing the gate = 500 calls/day × ~$0.0004 ≈ **$6/month**, or about $8 with share escalations.
- AI §11 moves to post-beta unchanged.

## 6. Week-1 50-screenshot reality test (R4d): REVISE (concrete)
- **Set:** 25 flyers (at least 10 stylised or text-over-image) and 25 chats (at least 10 with day headers and at least 5 negotiations), all from real phones.
- **OCR:** ML Kit text exported from the Android dev build's debug screen, which the trigger spike needs anyway. Tesseract would be a biased stand-in.
- **Harness:** a Python script runs each item text-only and with the image through Haiku plus the server resolver. Results are hand-scored on title, date, time and "Not sure".
- **Outputs:** accuracy per arm, "Not sure" rate, chat-anchor accuracy, tokens and p50/p95 latency.
- **Decisions it settles:**
  - The §2 image rule.
  - If chat-anchor accuracy is below 80%, every chat date becomes `needs_review`.
  - If text-path p50 is above 3 s, that number goes to the platform owner.
- These 50 items also become the "own" half of the eval set.

## 7. Embeddings (R7, C14, C19): CONCEDE
The beta uses **FTS5 only**, with the trigram tokenizer so OCR typos still match, ranked by BM25 over OCR text and the extracted title. There is no vector table, ONNX runtime or sqlite-vec. `ocr_text` is stored, so embeddings can be added later as a backfill job without changing the schema. All search runs on the device and offline.

## 8. Eval (R12): CONCEDE, with one addition
- **Set:** 150 images (100 synthetic plus the 50 from week 1), single runs.
- **Hard gates:**
  1. The date-resolver table, about 60 pure-code cases with no labelling: rollover, DST in both directions, this/next, 12/24 h, D/M ambiguity, chat headers, 12am.
  2. No network for sensitive images.
- **Report only:** everything else.

## 9. Privacy and minor items (R10, C16, C18)
- **R10: CONCEDE.** Redaction does not remove names. The copy must say names are sent, give the verified retention period (D3) and say the guard is English-only. "Send anyway" is dropped.
- **C16:** the text-path budget stays at p50 2.5 s / p95 5 s from the moment the image is available. R2's "share-to-card ≤ 2 s" is not reachable with a model round trip. Proposal: show a "Reading…" card within 1 s and the filled card at p50 ≤ 3 s.
- **C18 + R5:** AI-PROPOSE emits up to 3 alarm times as minute offsets for one calendar event. The day-before time follows actions §3.
