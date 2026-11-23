# 2 — AI pipeline design (Round 2, AI pipeline designer)

Scope: F2, F3, F5 (offsets only), F6, F7(b), F8 counts. Design only; schemas are illustrative. Principle applied throughout: the **model reads and proposes**, **code validates and resolves**, **the user confirms**.

Pricing below was checked against Anthropic's official pricing page (platform.claude.com/docs/en/about-claude/pricing, fetched 2026-11-18). Every other number marked *(est.)* is an estimate, not a measurement.

## 0. Pipeline at a glance (stable stage IDs)

| ID | Stage | Where | Model? |
|---|---|---|---|
| AI-INGEST | Receive image, capture time, user TZ/locale; SHA-256 | device | no |
| AI-DEDUP | Exact + near-duplicate check | device | no |
| AI-OCR | Text + line boxes + per-line OCR confidence | device | OCR engine (not an LLM) |
| AI-SENSITIVE | Sensitive-content guard → `local_only` | device | no (rules) |
| AI-GATE | Cheap "could this be actionable?" check; local pre-parse of dates | device | no |
| AI-REDACT | Mask emails, phone numbers, long digit strings in text to be sent | device | no |
| AI-EXTRACT | One call: classify + extract typed fields + verbatim evidence | server → LLM API | yes |
| AI-ESCALATE | Re-run AI-EXTRACT with the image (vision) or a stronger model | server → LLM API | yes |
| AI-GROUND | Check every evidence string really appears in the OCR text | server | no |
| AI-RESOLVE | Turn raw date/time strings into ISO datetimes (F3) | server (pure lib, also on device) | no |
| AI-VALIDATE | Schema, range, consistency checks | server | no |
| AI-CONF | Combine signals → per-field status + card decision | server | no |
| AI-PROPOSE | Build ≤3 action cards + deadline-ladder offsets (F5) | server | no |
| AI-EMBED | Sentence embedding of OCR text | device | small embedding model |
| AI-INDEX | Full-text index (FTS5) + vector store | device | no |
| AI-BACKLOG | Batch scheduler for imports | device + server | no |

There is **no summary stage**. No beta feature needs one: the feed shows class + extracted title (or first OCR line), and search runs on OCR text + embeddings.

## 1. Decision: OCR-first, vision only on escalation

**Decision: on-device OCR first, send text (not pixels) to a small text model; escalate to a vision call for about 10–15% of screenshots (est.).**

| | OCR-first (chosen) | Vision model on every screenshot |
|---|---|---|
| Privacy | Only redacted text leaves the device (~1–2 KB). The image stays local. | The full image leaves the device every time, including names, avatars and notifications in the status bar. |
| Cost per call (Haiku 5.5) | ~1,900 input tokens (est.) | ~3,500–4,000 input tokens (an image costs ~1,600–2,100 tokens after downscale, est. via the w×h/750 rule) |
| Latency | OCR 0.2–1 s on device + a shorter call (est.) | Upload ~0.3–1 MB + a longer call (est.) |
| Accuracy | Strong on flyers, chats, emails, LMS pages (mostly text). Weak on stylised posters, calendar grids, text over images. | Better on layout-dependent and stylised images. |
| Other gains | OCR text is needed anyway for F6 search, AI-SENSITIVE, AI-GATE, AI-GROUND and AI-DEDUP | — |

The deciding point: the sensitive guard (F7b) **must run before anything leaves the device**, and it needs text. So OCR on the device is required in any design. Once that text exists, sending pixels on every call buys accuracy only on the minority of layout-heavy images, at about twice the tokens and a much larger privacy cost.

OCR engine depends on the platform choice in Round 2: Apple Vision text recognition (iOS), ML Kit Text Recognition v2 (Android), or Tesseract.js / a WASM build if the app is a PWA (slower, est. 2–5 s; this is a latency risk for the PWA option).

**AI-ESCALATE triggers** (all deterministic): mean OCR line confidence < 0.6; fewer than 15 words but a large image area with text; the class is event/deadline but `start` failed AI-GROUND or AI-RESOLVE; the text looks like a grid (≥3 weekday headers or ≥10 lone numbers 1–31, which suggests a calendar or timetable). Escalation sends a downscaled image (long edge ≤1,568 px, EXIF stripped, status bar cropped) **only if** the image is not `local_only` and (it came from share/import, which is user-initiated) or (the user turned on "use image for hard cases"). Otherwise the card shows the flagged fields and gives no further guess.

## 2. AI-SENSITIVE and AI-REDACT (before any network)

Rules run on the OCR text plus the source app when the OS exposes it:
- Luhn-valid 13–19 digit runs; SSN / national-ID patterns; IBAN / routing+account pairs; "one-time code", "verification code", "password", "PIN"; bank / brokerage / health-portal keywords together with currency amounts or lab-value patterns; known banking, password-manager or 2FA apps as the source.
- Hit → `local_only = true`: OCR, embedding and the library entry stay local; **no API call, no cloud-derived proposal**. The card offers manual "Make event / reminder"; the local AI-RESOLVE may pre-fill dates from the text (pure code, nothing sent).
- **Flag for chair:** FEATURES lists "private messages" as sensitive, but the magic moment is a group-chat plan. Proposal: chat screenshots are **not** `local_only` by default. AI-REDACT masks phone numbers and emails, and a user toggle "never send chat screenshots" exists. The chair must rule on this.

AI-REDACT replaces emails, phone numbers and digit runs ≥7 with typed placeholders (`[PHONE_1]`), keeps the map on the device, and restores the values on the card if the model cites them. **Bytes sent per normal call:** redacted OCR text (median ~1.2 KB, est.), capture timestamp, IANA timezone, locale, OCR line order. No image, no filename, no device ID, no user ID beyond an opaque request ID.

## 3. AI-GATE (local, avoids sending nothing-to-do screenshots)

A high-recall check that passes if the text contains any of: a date pattern, a weekday or month name, a time pattern, relative words (today/tonight/tmrw/next week/EOD), or deadline words (due, RSVP, deadline, register by, expires, closes, submit, appointment). If nothing matches → classified **nothing-to-do locally**, no API call, silent in the library. Target: recall ≥0.98 on the eval set (only ~2% of actionable screenshots wrongly dropped). The expected drop rate is ~40–60% of screenshots (est.: memes, UI, photos of text with no dates). F8 counts gate drops and later "manual make-reminder on a gated item" as the miss signal.

## 4. AI-EXTRACT: classification + typed extraction in one call

One call does both jobs, because the classification depends on the same reading as the extraction, and two calls would double latency. The call uses **structured outputs** (`output_config.format` with the JSON schema) so the reply must parse. The model returns **raw strings plus evidence**, never computed datetimes.

```python
from pydantic import BaseModel, Field
from typing import Literal, Optional

Conf = Literal["high", "medium", "low"]          # coarse labels; model numbers are poorly calibrated

class Evidence(BaseModel):
    text: str = Field(description="verbatim substring of the OCR text this field came from")
    line: int                                       # OCR line index

class RawWhen(BaseModel):
    date_text: Optional[str] = None                 # "Fri 11/21", "tmrw", "Nov 21"
    time_text: Optional[str] = None                 # "7", "7-9pm", "noon"
    tz_text: Optional[str] = None                   # "CST", "ET" — only if printed
    evidence: list[Evidence]
    conf: Conf

class Field_(BaseModel):
    value: Optional[str] = None                     # None = absent from screenshot (never invent)
    evidence: Optional[Evidence] = None
    conf: Conf

class EventProposal(BaseModel):
    kind: Literal["event"]
    title: Field_
    start: RawWhen
    end: Optional[RawWhen] = None
    location: Field_
    all_day_hint: bool = False

class DeadlineProposal(BaseModel):
    kind: Literal["deadline"]
    title: Field_                                   # "RSVP for Pizza Night", "HW 5 due"
    due: RawWhen
    related_to: Optional[int] = None                # index of the event this RSVP belongs to

class ExtractResult(BaseModel):
    screen_class: Literal["event", "deadline", "nothing", "sensitive", "unsure"]
    class_conf: Conf
    source_hint: Optional[str] = None               # "Instagram flyer", "Canvas", "group chat"
    actions: list[EventProposal | DeadlineProposal] = Field(max_length=3)
    notes_for_user: Optional[str] = Field(None, max_length=140)  # e.g. "two dates shown; picked the event date"
```

`screen_class = "sensitive"` is a second line of defence: if the model sees sensitive content the rules missed, code drops all proposals and marks the item `local_only` from then on. That data was already sent once, so F8 logs it as a guard miss so the rules can be improved.

System prompt (frozen, cache-eligible) rules: copy evidence verbatim; leave a field null rather than infer it; do not compute dates; at most 3 actions; an RSVP / registration deadline next to an event is a separate `DeadlineProposal` with `related_to` set; past-tense recaps ("thanks for coming") → nothing.

## 5. AI-RESOLVE: deterministic date/time rules (F3)

A pure function `resolve(raw: RawWhen, anchor: datetime, tz: ZoneInfo, locale) -> Resolved` built on Python `zoneinfo` and a small hand-written grammar (about 40 rules) that is fully covered by the test table. Each output carries `assumptions: list[str]` shown on the card.

- **Anchor** = capture time (EXIF / file timestamp, else import time) in the user's current IANA timezone. It is **never** "now" for backlog items.
- **Relative words:** today / tonight (tonight with no time → 19:00 + flag) / tmrw / tomorrow / "day after tomorrow" are relative to the anchor date. A capture between 00:00 and 04:00 makes "tonight" and "tomorrow" ambiguous → flag.
- **Weekdays:** bare "Fri" or "this Fri" = the next Friday on or after the anchor date (same day if the anchor is a Friday and the time is still ahead, else +7). "next Fri" = the Friday of the next calendar week (Monday-start); it is **always flagged** because usage varies between people.
- **Numeric dates:** locale order (US M/D). If both parts are ≤12 and the locale is not US, or the source looks foreign (from F8 later) → flag `day_month_ambiguous`. Two-digit years → 20YY.
- **Missing year:** the first occurrence on or after (anchor − 7 days). The 7-day grace keeps "Dec 31" captured on Jan 2 in the old year as a past item. Year rollover: "Jan 5" captured on Dec 20 → next year, with an assumption shown.
- **Weekday + date conflict** ("Fri 11/20" but 11/20 is a Thursday) → keep the date, flag both, `needs_review`.
- **Missing AM/PM:** 7–11 → PM if the context is an event, AM if the text has "breakfast" or "morning"; 1–6 → PM; 12 → noon. Always shown as an assumption. 24-hour times ("19:00") are taken as-is.
- **Ranges** "7–9pm" → the meridiem spreads backwards to the start. An end before the start → +1 day (overnight), flagged.
- **Missing time:** an event becomes all-day (flagged); a deadline becomes 23:59 local ("assumed end of day").
- **Midnight / "12am Friday"** → 00:00 at the start of Friday, but always `needs_review` because people often mean Thursday night.
- **Time zones:** a printed abbreviation maps through a table. Ambiguous ones (CST, IST, BST) → resolve to the user's region if it fits, else flag. No abbreviation → the user's timezone, with "times in your time zone" shown when the source hints at another place.
- **DST:** a non-existent local time (spring forward) moves forward 1 h + flag; an ambiguous time (fall back) → the first occurrence (`fold=0`) + flag.
- **Past result:** resolved start < now → the card is "Past: no action" (no notification). Backlog items are always checked against now before any notification.
- **Deadline ladder (F5):** code computes day-before 09:00, morning-of 08:00 and due − 2 h. Any offset in the past is dropped, and the remaining offsets are shown and can be edited.

The test table (owned by the eval plan) must include: year rollover, DST in both directions, this/next, 12/24 h, "noon"/"midnight", D/M ambiguity, a tz abbreviation, a weekday/date conflict, and a backlog anchor years in the past.

## 6. AI-GROUND, AI-VALIDATE, AI-CONF: confidence and "not sure"

Self-reported model confidence is used as **one input only**. The status of each field comes from code:

| Signal | Effect |
|---|---|
| Evidence not found in OCR text (fuzzy match ≥0.9 after whitespace/case normalisation) | Field cleared → `missing`. This enforces "never invent". |
| AI-RESOLVE failed | `needs_review` |
| AI-RESOLVE made an assumption | `assumed` (yellow, can be edited, does not block confirm) |
| Model conf = low, or OCR line conf < 0.5 on the evidence line | `needs_review` |
| Validation failure: end < start, start > 2 years out, title > 120 characters or empty | `needs_review` |
| Otherwise | `ok` |

Card-level decisions:
- **Propose with notification** only if the class is event/deadline, class_conf ≥ medium, `start`/`due` is not `missing`, and the item is not past.
- **"Not sure" card** (in the library, no push notification) if the class is `unsure`, class_conf is low, or the key datetime is `missing`. It shows "Looks like it might be an event. Make one?" with the fields that are known.
- **Confirm button is disabled** while any field is `needs_review`, until the user touches that field (F2b).
- The thresholds above are starting points. F8's per-field edit rate per status level is used to retune them; target: fields marked `ok` edited in <5% of confirmations.

## 7. AI-DEDUP: exact and near duplicates

- **Exact:** SHA-256 of the bytes, plus the platform asset ID → never processed twice (F1d).
- **Near duplicate** (screenshot again, status bar clock changed, cropped, re-shared): 64-bit dHash on the image with the status bar cropped, Hamming ≤ 6, **and** OCR token Jaccard ≥ 0.85 → linked to the original, with no new API call and no new card. Hash alone gives false matches on similar layouts (two different Canvas pages), so both checks are needed.
- **Proposal level:** a new proposal whose normalised title plus resolved start (±30 min) matches an open or confirmed action → "Already added" or merged into the existing card. This catches the same event screenshotted from two apps.
- Cost: a dHash is 8 bytes; comparing against 10k items takes a few ms on device with a BK-tree.

## 8. AI-EMBED and AI-INDEX: search (F6)

- **Model:** `bge-small-en-v1.5` or `all-MiniLM-L6-v2` class (384 dimensions, ~22–33 M parameters, ~25–35 MB quantised, est.), run on device through Core ML / TFLite / ONNX Runtime, or transformers.js in a PWA. Query embeddings are also computed on device.
- **Why on device:** it covers `local_only` items the same way as others, search needs no network, there is no per-query cost, and no extra bytes leave the device. A server embedding API would send every OCR text, including gated "nothing" items, for a feature that a small model handles well enough on short text (English-only for the beta; multilingual is a later swap).
- **Input:** the first ~256 tokens of OCR text, plus the extracted title when there is one.
- **Storage per 10,000 screenshots:** 384 × int8 = 384 B per vector → **3.8 MB** (float32: 15.4 MB). OCR text ~1.5 KB → ~15 MB. SQLite FTS5 index ~5–10 MB. Metadata and hashes < 2 MB. **Total ≈ 25–35 MB (est.)**, excluding images.
- **Query:** brute-force cosine over 10k int8 vectors ≈ 5–20 ms on a phone (est.), so no ANN index is needed at this scale. Hybrid ranking = 0.5·BM25 (FTS5) + 0.5·cosine, normalised. Target search p95 ≤ 300 ms on device (proposed for DESIGN.md).

## 9. Model choices and fallbacks

| Role | Primary | Fallback | Why |
|---|---|---|---|
| AI-EXTRACT (text) | **Claude Haiku 5.5** (`claude-haiku-5-5`), effort `low` | Claude Sonnet 5.5 on repeated validation failure | The task is short, structured reading. Haiku costs $0.10/$0.50 per MTok (verified) |
| AI-ESCALATE (vision) | Haiku 5.5 with the image | **Claude Sonnet 5.5** (`claude-sonnet-5-5`, $2/$10 verified) if the Haiku vision result still fails AI-GROUND or AI-RESOLVE | Hard layouts need more capability |
| Backlog | Haiku 5.5 via **Message Batches API** (50% off: $0.05/$0.25 verified) | real-time Haiku for items predicted to be upcoming | Cost |
| API outage / rate limit | Queue with retry. After 60 s, show a **"basic" card** from local AI-GATE + AI-RESOLVE (dates only, title = first OCR line, all fields `needs_review`) | — | The core loop degrades instead of failing silently (F1c spirit) |
| On-device LLM | Not in beta | Later: Apple Foundation Models / Gemini Nano for `local_only` proposals | These run only on recent flagship hardware, which conflicts with "works on ordinary phones" |

Notes for the builder: Haiku 5.5 runs adaptive thinking by default, so set `output_config.effort="low"` and count thinking tokens as output. Refusals on Haiku have no server-side fallback, so handle `stop_reason == "refusal"` in code (route to the "Not sure" card). Use one provider SDK (`anthropic`) for the beta. A second provider is not worth the extra code for a solo developer. Anthropic's data-retention terms for this use must be checked and stated in the F7 onboarding copy; that is **not verified here**.

## 10. Model vs deterministic code responsibility

| Responsibility | Model | Code |
|---|---|---|
| Reading text from pixels | — (OCR engine) / vision model only on escalation | OCR engine |
| Sensitive detection | backup signal only | **primary** (rules, before network) |
| "Could be actionable?" | — | AI-GATE |
| Class (event / deadline / nothing / unsure) | **proposes** | overrides on validation; enforces `local_only` |
| Field values (title, location, raw date strings) | **proposes** with verbatim evidence | AI-GROUND verifies every one |
| Date/time/TZ arithmetic | never | AI-RESOLVE |
| Confidence status per field | one input | **decides** (AI-CONF) |
| Duplicate detection | — | AI-DEDUP |
| Reminder offsets (F5) | — | AI-PROPOSE |
| Writing to calendar/reminders | never | action engine, after the user taps |
| Embeddings | small embedding model | ranking, storage |

## 11. AI-BACKLOG: importing 10,000+

1. **Local pass first, over everything** (on device, background, while charging + on Wi-Fi when possible): hash, dedup, OCR, sensitive, gate, embed, index. Search works over the whole backlog before any API spend. Throughput is ~3–10 images/s on a mid-range phone (est.) → 10k in ~20–60 min. Show progress, and resume after the app is killed.
2. **Local pre-resolve:** run AI-RESOLVE on the dates found by AI-GATE. Items whose dates **all** resolve to the past (with the backlog anchor) → "Past" and **no API call**. This is expected to remove most of an old backlog (est. >80% of gated items older than 60 days).
3. **Priority queue for the remainder:** (a) any date resolving within the next 30 days → real-time Haiku, newest capture first; (b) future dates beyond 30 days → Batch API; (c) gated items with no resolvable date → Batch API, newest first, lowest priority.
4. **No hard daily cap** (complaint 4). The server limits by tokens/minute per user to protect the shared rate limit, with fair round-robin between users so one 10k import cannot starve others' live screenshots. Live screenshots always jump ahead of the backlog.
5. **No per-item notifications** for backlog results: one digest ("9 upcoming events and 4 deadlines found in your old screenshots").

## 12. Latency targets (screenshot → action card)

Measured from the moment the app has the image (detection delay depends on the platform and is owned by Round 2):

| Path | p50 | p95 |
|---|---|---|
| Local stages (dedup + OCR + sensitive + gate + redact) | 0.6 s | 1.5 s (PWA: 4 s) |
| AI-EXTRACT round trip (Haiku, ~2k in / ~450 out, est.) | 1.5 s | 3.5 s |
| Ground + resolve + validate + propose | <50 ms | 100 ms |
| **Total, text path** | **≤2.5 s** | **≤5 s** |
| **Total, with vision escalation** | ≤6 s | ≤12 s |
| Gated "nothing" (no API) | ≤1 s | ≤2 s |

The API figures are estimates and must be measured in the first prototype. F8 records time-to-card.

## 13. Cost per 100 screenshots

**Assumptions (est.):** 50% of screenshots pass AI-GATE (50 calls); per text call ~1,500-token frozen system prompt + schema and ~400 tokens of OCR text = 1,900 input, plus ~450 output including low-effort thinking. Costs are computed **without** prompt caching (conservative; caching applies only if the prefix meets Haiku's minimum cacheable length). 12% of called items escalate to Haiku vision (+2,000 image tokens); 3% of called items go to Sonnet 5.5 vision (4,000 in / 500 out). Embeddings and OCR are on device, so $0.

| Item | Calc | $ |
|---|---|---|
| Haiku text, 50 calls | 50 × (1,900 × $0.10 + 450 × $0.50)/1M | 0.0208 |
| Haiku vision, 6 calls | 6 × (3,900 × $0.10 + 450 × $0.50)/1M | 0.0037 |
| Sonnet vision, 1.5 calls | 1.5 × (4,000 × $2 + 500 × $10)/1M | 0.0195 |
| **Live total** | | **≈ $0.044 / 100 screenshots** |
| Backlog (Batch −50%, ~80% of gated items removed as past) | | ≈ $0.005–0.01 / 100 → **≈ $0.50–1.00 per 10k import** |

A heavy user (30/day) → ~$0.40/month (est.). The Sonnet escalations are about 45% of the cost, so the escalation rate is the cost metric to watch in F8. With no gate and no caching, the worst case is ~$0.09 / 100.

## 14. Open items for the chair

1. Whether chat screenshots count as sensitive (§2).
2. The platform choice sets the OCR engine and PWA latency (§1, §12).
3. Image escalation policy for auto-detected screenshots: opt-in toggle (proposed) or on by default.
4. Data-retention statement for the API provider: verify before writing the F7 onboarding copy.
