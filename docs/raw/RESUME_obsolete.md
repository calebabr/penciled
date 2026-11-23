# STATUS: council complete (2026-11-19). All four deliverables written; this resume file is obsolete.

# RESUME — council status (paused 2026-11-18 at ~80% of 5-hour limit, per user's "end at 85%")

## Done
- Round 1: raw/1a_*.md, raw/1b_prioritizer.md; FEATURES.md written and amended (Round 2).
- Round 2: raw/2_ui.md, 2_platform.md, 2_architecture.md, 2_ai_pipeline.md, 2_actions.md, 2_privacy.md.
- Round 3: raw/3_scalability.md, raw/3_eval.md.
- Round 4: raw/4_redteam.md; rebuttals raw/4_rebuttal_{features,ui,architecture,ai,scale}.md. All five received.
- raw/chair_decisions.md (D1–D9).
- UI brainstorm using the frontend-design plugin skill: agent a6cda53a41f07a03e was left running; output should land at raw/4_design_brainstorm.md (check it exists). "Impeccable" skill was not found anywhere on disk or in claude.ai skills; ask the user where it lives.

## Update (usage hit 85% — stopped)
- Impeccable skill is installed (~/.claude/skills/impeccable) and listed. The frontend-design brainstorm finished: raw/4_design_brainstorm.md ("Pencil, highlighter, ink" identity, ink-in confirm animation, 7 exact UI.md edits).
- FIRST on resume: invoke the `impeccable` skill (critique/audit mode) on raw/2_ui.md + raw/4_rebuttal_ui.md + raw/4_design_brainstorm.md; look back at earlier UI decisions (4-screen scope, tokens, accessibility, states); save to raw/4_impeccable_review.md; then merge into the UI.md plan. Per user: use it for UI brainstorming/feature ideation too.

- SCOPE OF THE IMPECCABLE REVIEW (user, confirmed): review everything already created that concerns UI: raw/2_ui.md, raw/4_rebuttal_ui.md, raw/4_design_brainstorm.md, UI-facing parts of raw/3_eval.md (QA-SNAP/PERF/A11Y), UI implications in raw/2_privacy.md and raw/2_actions.md (copy, permissions, error/undo states), and FEATURES.md acceptance criteria that shape UI. Do not run it until the user says to resume.

## NOT done (do in this order)
1. Adopt rebuttal revisions into FEATURES.md (summary in raw/4_rebuttal_features.md: iOS = share sheet + catch-up on open, no App Intent; F5 ladder merged into F4 as one calendar item with up to 3 alarms; F1(e) no pre-install screenshots, import cap 20; F6 = FTS5 only, meaning search to post-beta; F3 day-header anchoring, non-blocking inferred year; images sent by default for share/import except sensitive/chat, auto-detect opt-in per rebuttal_ai (amend D2); F7 drop "Send anyway"; honest retention copy). Add D10 etc. to chair_decisions.md. Resolve red-team contradictions C1–C24 per raw/4_rebuttal_architecture.md.
2. Mid-run addition (user's second paste): evaluate (a) smart resurfacing and (b) calibrated confidence gating.
   - Two agents were started then STOPPED to save usage; rerun them: feature prioritizer (opus ≤600w → raw/5_prio_prob_features.md) and AI pipeline designer (opus ≤1,000w → raw/5_ai_prob_features.md), in parallel. Prompts: see original user paste (resurfacing: priors + Bayesian/survival, cold start, privacy, offline eval, day-one event log; gating: calibration method, per-field roll-up, thresholds, ECE/reliability, data needs).
   - Then red team ≤400w quick pass (no rebuttal) → raw/5_redteam_prob.md.
   - Chair: update FEATURES.md with a decision per feature (beta / post-beta / rejected) with reasons.
3. Round 5: write UI.md, DESIGN.md, BUILD_HANDOFF.md per the original spec. Fold in: calibration metrics + resurfacing metrics (act-on rate, dismiss rate) in eval section; UI states for confidence ("needs a look", ready card, ask question) and notification/resurfacing design; BUILD_HANDOFF components with S/M/L sizing, calibration placed before the confidence gate in the dependency graph, labeled-data requirement in the eval set, deferred features still listed as post-beta components, behavior events logged from day one. Apply design-brainstorm edits to UI tokens.
4. Final verification checklist from the original prompt (nothing built/installed; every beta feature traces to evidence; every screen maps to a component; platform claims link to official docs — mark memory-sourced links "verify"; no component above L without justification).

## Known caveats to carry into docs
- Evidence thin (n=55 survey; secondhand Mottelson figure; no Reddit/Play text).
- Doc links in 2_actions.md and 2_privacy.md were from memory; provider retention terms unverified.
- Agent word caps exceeded: privacy, platform, architecture, eval.
- Build constraints: user is on Windows, no Mac; iOS via EAS cloud builds.
