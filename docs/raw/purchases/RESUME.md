# Purchases council: paused mid-finalization (user shut down computer)

Done: raw/purchases/1_analyst.md and 1_prioritizer.md. Chair decisions (binding) are in the editor prompt summarized below. The combined design pass (2_design.md) was stopped and skipped by user choice.

INTERRUPTED: the finalizing editor agent was stopped mid-run. It may have made PARTIAL edits to FEATURES.md, UI.md, DESIGN.md, BUILD_HANDOFF.md, raw/chair_decisions.md (D24), and may or may not have created SPRINT_IMPACT.md. Edits are tagged "(added: purchases extension)". On resume: grep those four docs and chair_decisions.md for "added: purchases extension" and "D24" to see what landed, then re-run the editor only for what is missing (do not duplicate). 

Binding decisions:
- BETA: zero-build passthrough (printed "Return by <date>" on a guard-passing receipt = ordinary deadline card; no new class, no policy inference); day-one enum-only logging in shared contracts BEFORE CP0 freeze on Nov 25 (nothing-to-do subtype: receipt_order/shipping/booking/meme/other; guard-block reason counts; deadline_origin=printed_return_by; confirm/edit/dismiss rates); 10–15 receipt fixtures added to the ~150-image eval set. Promotion trigger: receipts >=15% of processed screenshots AND >=30% show a printed return date.
- POST-BETA #1 (with receipt->expense): Purchase type slice 1 = extraction + return window from a hand-curated retailer policy table (unknown retailer => ask user; model never invents a deadline); slice 2 = warranty (user input/printed terms).
- REJECTED w/ triggers: recall matching (CPSC fields empty, fuzzy match, false alarms); "things I own" view + insurance export.
- Outputs still required: SPRINT_IMPACT.md (expect <=~0.5 session, date Jan 13–15 holds, nothing displaced; list SPRINT_PLAN.md changes, do not edit it); verification that no deadline/recall match reaches the user without deterministic validation.

Also pending: user said yes to a lean follow-up pass on pricing/tier design (monetization). Not started.
