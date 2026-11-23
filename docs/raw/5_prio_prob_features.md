# 5. Probabilistic features: prioritization (Feature Prioritizer)

Basis: FEATURES.md after Round 4 (7 features, 4 screens, FTS5, no backlog), 1b scoring scale (V value, D differentiation, R reliability, C cost by beta, 5 = cheap), D10/D11. Same caveat as 1b: V is ±1 because the evidence is thin (n=55).

## Scores

| Feature | V | D | R | C | Total |
|---|---|---|---|---|---|
| 1. Smart resurfacing (learned timing) | 3 | 4 | 2 | 1 | 10 |
| 2. Calibrated confidence gating (full, adaptive) | 4 | 4 | 3 | 2 | 13 |
| 2a. Beta slice (fixed, eval-calibrated thresholds) | 4 | 3 | 4 | 4 | 15 |

**1. Resurfacing.** *V3:* the examples it was pitched with (recipes on weekends, receipts at month end) are post-beta categories. In beta, events and deadlines already carry their own time, and F5 sets alarms from it. That leaves only one thing to time: the nudge for an unconfirmed draft. *D4:* nobody ships it, but 1b #15 and the Rejected list both record that proactive features go unnoticed (Magic Cue poll). *R2:* with roughly 20 testers and a few events each per week, per-user learning stays on its defaults for the whole beta. A learned model would add risk with no measurable gain. *C1:* needs a scheduler, nudge-budget logic, a notification surface in addition to F1's "ready" notification, and a spam guard. That is about 1.5–2 weeks of a solo build.
**Decision: POST-BETA.** The beta gets no learned slice. If testers leave drafts unconfirmed, a fixed rule (one nudge at 18:00 the same day, never repeated) is the most I would accept, and only after F8 shows drafts going stale. **Displaces:** F6 (the first cut) and part of F8. **Magic moment:** not strengthened. The moment happens seconds after capture, not hours later, and an extra notification works against the "never spammy" constraint.

**2. Confidence gating.** F2(b) already requires flagged low-confidence fields, so the slice mostly makes that requirement honest:
- Each field's score comes from **deterministic signals**, not the model's self-reported confidence, which is poorly calibrated:
  - validator pass
  - the date/time string appears verbatim in the OCR text
  - the F3 parse is unambiguous
  - the model's own score, used only as one input
- Calibrate once on the ~150-image eval set (D10) with binned reliability (isotonic if the bins allow it).
- Set **per-field** thresholds in a config table. Do not set them per action type yet, because about 150 images × 2 types is too few labels per cell.
- Three card states, using the vocabulary already chosen: Ready to add / Draft with highlighted fields / "Not sure". The "Is this an event on Dec 4?" question goes inside the Confirm sheet as a flagged field, not on a new screen. D11 limits the beta to 4 screens.
- **Rule:** the user still confirms every action, and a below-threshold field always blocks or highlights. It is never auto-filled silently.

**Decision: SPLIT.** 2a goes into **BETA** inside F2, at about 3–4 days, mostly eval-harness work that D10 already pays for. Adaptive per-user and per-type thresholds learned from corrections are **POST-BETA**, merged into queue item 3 (Teach-by-correction). They only start once a field has about 50 or more labelled outcomes. Automatic adaptation may only move a threshold toward flagging *more*. Loosening a threshold needs a human review of the eval set. **Displaces:** nothing at slice size. If the build slips, the eval-calibration step is the one to drop, falling back to hand-set thresholds. **Magic moment:** strengthened directly. "One highlighted field to fix" only builds trust if the highlight is on the field that is actually wrong.

## Data each needs
- **Resurfacing:**
  - per-notification timestamps (sent, opened, dismissed, snoozed) and the time from draft to confirm
  - hour-of-week bucket, class
  - weeks of history per user, which the beta cannot supply
- **Gating:**
  - per-field ground-truth labels from the eval set
  - in beta, an edit or no-edit on confirm counts as an implicit label (noisy, because users skip checks)
  - model and prompt version, so calibration can be redone whenever the model changes

## LOG FROM DAY ONE (both features; counts and scores only, no content, extends F8)
Per field:
- raw score and each signal (validator, OCR-verbatim match, parse ambiguity, model score)
- threshold version
- whether the field was flagged
- outcome: untouched / edited / cleared / filled from blank

Per card:
- state shown
- confirm / dismiss / ignore
- Undo within 24 h, which counts as a strong "wrong" label
- time from card to confirm

Per notification:
- sent, opened and dismissed timestamps
- local hour-of-week bucket
- class

Everywhere: `model_version`, `prompt_version`, `schema_version`.

Logging costs about half a day now. Without these logs, both post-beta versions start with no data.
