# 5. Probabilistic features: Red team

## 1. Smart resurfacing: biggest risk = nudges burn notification trust, and with it the core push
**Severity: High. Likelihood: Medium-High.**
If a nudge feels random or naggy, the user turns off notifications for the whole app. Doing that also kills F1's "Ready to add" push, which carries the magic moment. AI-RESURF-07's 20% uniform-random slots *deliberately* send nudges at bad times. At beta scale they buy nothing: about 20 testers × about 5 nudges × 20% is roughly 20 random events, too few for inverse-propensity replay. (The AI file assumes about 300 testers and the prioritizer about 20. Resolve this before any ship bar is quoted.) Nudges about screenshots the user forgot they took can also feel creepy.
**Cut/guardrail:**
- No random slots in beta.
- No resurfacing notifications in beta.
- Resurfacing never triggers its own permission prompt. It only rides the permission F1 already asked for, and only post-beta.

## 2. Calibrated gating: biggest risk = overconfident "Ready to add" on rare screenshot types
**Severity: High. Likelihood: Medium.**
The eval set has about 150 images and only about 30 errors. One pooled model fitted to that learns the common case. Rare types score high because they borrow the common case's signals, so they land in "Ready to add" while wrong. That is the C_wrong = 10 silent-error case the cost rule exists to prevent. Rare types include:
- handwritten or low-contrast text
- non-English text
- multi-event posters
- relative dates ("next Fri")

A second problem: implicit labels (an unedited confirm counts as "correct") leak optimism, because users check fields marked ok less.
**Cut/guardrail:**
- Hard caps before any score:
  - A required field with no verbatim or fuzzy source match can never be "Ready".
  - class_conf below threshold, or a type outside the eval set's coverage, means at most "Ask".
- The Platt model stays offline-only in beta. Do not use the prioritizer's isotonic option: about 30 errors is too few for it.
- Implicit labels may only *tighten* thresholds.
- Cut the 2% "Is this right?" audit from beta. It adds friction to cards that are correct.

**Secondary risk: "Ask question" becomes a friction wall.**
- Confirm is blocked until every flagged field is touched.
- Keep the 40% over-asking alarm.
- Let one tap on "Looks right" clear a flag.

## Verdicts
- **Prioritizer's split: agree.**
  - The 2a slice goes into beta: rule-based signals mapped to 3 states, fixed thresholds, and the user still confirms everything.
  - Adaptive and per-user thresholds are post-beta, tighten-only.
  - Resurfacing is post-beta. If the build slips, the eval-calibration step is the right thing to drop.
- **Resurfacing logged-only in beta: yes, in shadow mode.**
  - Compute the would-nudge decision from the cold-start rule and log `nudge_scheduled` with `shown=false`. Never send it.
  - Also log F1 notification sent, opened and dismissed, plus the time from draft to confirm.
  - This costs about half a day and answers whether drafts go stale at all, before anyone builds a scheduler.
  - The prioritizer's fallback (one nudge at 18:00) becomes allowed only if F8 shows more than about 30% of drafts left unconfirmed for over 24 h.
