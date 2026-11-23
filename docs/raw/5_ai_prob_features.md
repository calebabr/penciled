# 5 — AI probabilistic features (design only)

Candidates only; FEATURES.md rejects resurfacing for beta (Chair must re-admit). Numbers *(est.)*. Logs are enums only.

## 1. Smart resurfacing (AI-RESURF)

**AI-RESURF-01 Scope.** Re-nudge an unconfirmed **Draft** card. Calendar alarms belong to the OS and are out of scope.

**AI-RESURF-02 Model: Beta priors with Bayesian updating, not survival.** One user gives about 5–30 nudges per beta, which is far too few for a time-to-event model with censoring.
- **Cells:** action_type × 4-hour time block (6 blocks), each holding `Beta(α,β)` over P(confirmed within 24 h | nudged in that block).
- **Prior:** the population rate at strength n₀ = 10, so the user's own data dominates after about 10 nudges.
- **Scheduling:** the allowed block with the highest posterior mean before `start − 24 h` (deadlines: `due − 6 h`).

**AI-RESURF-03 Features.** action_type, lead bucket (<1 d / 1–3 d / 3–7 d / >7 d), time block, weekend, source (auto/share), nudge_index, snoozes. Nothing comes from screenshot content.

**AI-RESURF-04 Cold start.** If a card is still Draft 4 h after it was created and starts more than 24 h out, nudge once at the next 18:00 or 09:00, the same times as the F5 alarms.

**AI-RESURF-05 Placement.**
- **Phone:** keeps the posterior in a core.db `kv` row and schedules a local notification.
- **Server:** recomputes population priors from opt-in counts and returns them in the `/v1/extract` response. No new endpoint.

**AI-RESURF-06 Guardrails.**
- At most 2 nudges per day and 2 per card.
- Quiet hours 22:00–08:00, editable.
- Snooze backoff 4 h, then 12 h, then stop.
- Two dismissals of the same card stop nudges for it.
- If more than 60% of the last 10 nudges were dismissed, the daily cap is 1 for 7 days.
- Never nudge past items. Settings has an off switch.

**AI-RESURF-07 Replay evaluation.**
- **Unbiased replay:** 20% of nudges use a uniformly random allowed block, with its propensity logged. Candidate policies are scored by inverse-propensity replay on these events.
- **Metrics:** act-on rate (confirmed ≤24 h after a nudge), dismiss rate, median time-to-action, nudges per confirm, nudge opt-out rate.
- **Ship bar:** act-on rate at least 5 points above the default, with a bootstrap CI that excludes 0, and dismiss and opt-out rates no worse.

**AI-RESURF-08 Event log, from day one** (`behavior_event`, in core.db):
```
id, card_id, ts_utc, local_block, weekday,
event ENUM(card_created, notif_shown, notif_opened, nudge_scheduled, nudge_shown,
           nudge_opened, nudge_dismissed, snoozed, field_edited, confirmed, dismissed, undone),
action_type, lead_bucket, source, nudge_index, policy_id, propensity,
field ENUM?, gate_state ENUM?, conf_bucket 0-9?
```
- No free-text columns; a CI grep test enforces this.
- Upload is opt-in, as enum rows under a rotating install hash.
- The `field_edited` rows also feed AI-CALIB-05.

**Beta slice vs full version:**
- **Beta slice:** the log, the cold-start rule, the guardrails and the 20% randomisation. No learning.
- **Full version:** on-device posteriors, server priors, then Thompson sampling.

## 2. Calibrated confidence gating (AI-CALIB, AI-GATE)

**AI-CALIB-01 Raw score.** The model returns no logprobs, so each field gets a vector of signals:
- verbalized `conf` (high/med/low)
- source-substring match (exact / fuzzy ≥ 0.9 / none)
- AI-RESOLVE status (ok / assumed / needs_review / failed)
- OCR confidence of the evidence line
- whether escalation happened
- class_conf

Self-consistency (k = 3) triples cost under the $25 cap. It is measured **offline on the eval set only** and enters production only if it improves Brier by ≥0.02.

**AI-CALIB-02 Method: Platt-style logistic regression** maps the signals to p(field correct), as one pooled model with a field-type indicator.
- **Rejected:** temperature scaling needs logits, and isotonic overfits below about 1,000 labels per cell.
- **Where it runs:** the server's Python AI-CONF, with coefficients versioned with `prompt_version`. The phone only obeys the returned `gate_state` and `blocking`.

**AI-CALIB-03 Roll-up: min** over the required fields (title, start/due) and class_conf.
- **Why min:** errors share OCR lines and so are correlated, and a product would double-count them.
- **Full version:** a learned roll-up.

**AI-CALIB-04 Cost-weighted threshold.** Ask about a field when (1−p)·C_wrong > C_question. With C_wrong = 10 (a silent wrong calendar entry) and C_question = 1 (one tap), that means asking when **p < 0.90**. The ratio is a product decision.

**AI-CALIB-05 Adapting from corrections.**
- **Labels:** an edited field counts as wrong; a confirmed field with no edit counts as correct.
- **Bias fix:** confirmed-unedited labels under-count errors on fields marked ok, because users check them less. A 2% in-app audit of ok cards ("Is this right?") corrects for this.
- **Recalibration:** global, never per user, at each release, for cells with ≥50 labels. Each recalibration moves a threshold by at most ±0.05.

**AI-CALIB-06 Measurement.**
- **Reported per class and field:** reliability diagrams (5 equal-mass bins while n < 500, then 10), ECE and Brier, each with bootstrap CIs, plus EVAL-FLD-02/03.
- **Targets:** ECE ≤ 0.05, and Brier no worse than the rule mapping.

**AI-CALIB-07 Labels needed.**

| Data | Supports |
|---|---|
| Eval set: ~150 images, giving ~300 field labels and ~30 errors | one pooled Platt with 5-fold CV; card-level ECE only, ±0.05 |
| ~500 labels with ≥50 errors per field, about 1,500 confirmed cards (300 testers × 5) | per-field Platt and reliability diagrams |
| ≥1,000 labels with ≥100 errors per cell (post-beta) | isotonic calibration, learned roll-up |

**AI-GATE-01 States.** The hard rules come first: `local_only`, past and resolve-failure override everything below.

| State | Rule | Notification | Confirm |
|---|---|---|---|
| **Ready to add** | card score ≥ 0.90 | "Ready to add" push | enabled; `assumed` captions are non-blocking |
| **Ask question** | 1–2 required fields with 0.60 ≤ p < 0.90 | push shows the question ("Sat or Sun?") | blocked until each flagged field is touched |
| **Needs a look** | any field < 0.60, more than 2 flagged, or class unsure | none; card goes to the library as "Not sure" | manual |

**AI-GATE-02 Over-asking alarm.** If more than 40% of cards land in Ask question, review the cost ratio.

**Beta slice vs full version:**
- **Beta slice:** the rule-based AI-CONF (AI §6) mapped to the three states; the pooled Platt as an offline report only; `conf_bucket` and `field_edited` logged.
- **Full version:** the production Platt plus AI-CALIB-05 adaptation at about 1,500 labelled cards, then per-field, then isotonic.
