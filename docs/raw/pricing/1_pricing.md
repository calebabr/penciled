# Pricing and monetization: lean pass (design only, 2026-11-19)

Inputs: FEATURES.md, DESIGN.md §4–§5, raw/1a_competitors.md, raw/purchases/1_analyst.md, raw/3_scalability.md. Every figure marked *(est.)* is a model, not a measurement. The beta (SP-11, F8) replaces these figures with measured ones.

## 1. Reconciled unit economics

**Why the two figures disagree.** "$0.002 per screenshot" (DESIGN §5.8, EVAL-COST-01) is a **ceiling budget**: the mean must stay at or below it, p99 ≤ $0.01. It is not an estimate. The ~$0.13–0.15 per DAU-month (scalability §7) is a **bottom-up estimate**:
- Text call: $0.00042 uncached; ~$0.00029 with the 1,500-token prefix cached (Haiku 5.5, $0.10/$0.50 per MTok, DESIGN §4.5).
- Vision escalation: about $0.0008 per escalated call *(est., unverified image token count)*. At a 10% escalation rate that adds ~$0.00008 per call, for **~$0.00037 per call**.
- AI-GATE passes 50%, so the cost is **~$0.00019 per screenshot**, about 1/10 of the budget.
- At 20 screenshots/day for 30 days: 600 × $0.00019 ≈ $0.11 for the LLM, plus ~$0.01 infra, ≈ **$0.12–0.15**. The two sources agree.

Pricing at the $0.002 ceiling would show $1.20 per DAU-month. That is a stress bound, not a plan.

| Profile *(est.)* | Screenshots/mo | Gate pass | Escalation | LLM | +infra | **Per user-month** |
|---|---|---|---|---|---|---|
| Light (5/day, 20 days) | 100 | 50% | 5% | $0.016 | $0.01 | **~$0.03** |
| Typical (20/day, 25 days) | 500 | 50% | 10% | $0.09 | $0.01 | **~$0.10** |
| Heavy (30/day, 30 days) | 900 | 60% | 20% | $0.24 | $0.01 | **~$0.25** |
| Abuse ceiling (100 calls/day quota × $0.002) | — | — | — | $6.00 | — | bounded by COMP-QUOTA |
| Backlog sweep, one-off 10k images via Batch API | — | — | — | $0.50–2 | — | Pro only |

**Blended per MAU** (mix 50% light / 40% typical / 10% heavy) ≈ **$0.08** *(est.)*. Caching saves ~30% per call. Escalation rate is the main cost lever.

## 2. Store fees

| Store | Subscription fee | Source |
|---|---|---|
| Apple, standard | 30% in year 1 of a subscriber's paid service, 15% after | [Small Business Program](https://developer.apple.com/app-store/small-business-program/). I could not fetch this page, so the figure is confirmed only by [RevenueCat](https://www.revenuecat.com/blog/engineering/app-store-fees) and [Adapty](https://adapty.io/blog/app-store-small-business-program/). **Verify.** |
| Apple, Small Business Program (≤$1M proceeds in the prior year; you must enroll yourself) | **15% from the first billing**, so the second-year drop gives no further benefit | same |
| Google Play | **10% + a 5% billing fee = 15%** on auto-renewing subscriptions (first $1M). A new new-vs-existing-install fee structure for other digital purchases took effect in the US on 2026-06-30. | [Play service fees](https://support.google.com/googleplay/android-developer/answer/112622) (fetched) |
| Pending | In Aug 2026 Apple proposed a US commission on link-out purchases: 15% in year 1, 10% on renewals. Not approved. | [Subscription Insider](https://www.subscriptioninsider.com/blog/apple-proposes-15-year-one-link-out-fee-10-on-subscription-renewals) (secondary) |

**Plan on 15% net on both stores.** Also budget for RevenueCat (free up to ~$2.5k monthly tracked revenue, then ~1%; *unverified*).

## 3. Recommended model: "core free forever, Pro for power features"

**Free tier:**
- Everything in the beta core loop: capture, event and deadline cards, F3 date resolution, Confirm and Undo, history, keyword library search, privacy controls.
- Imports of 20 per batch.
- **30 cloud extractions/day.** A typical user needs ~10.
  - At the cap, items are **queued and processed after local midnight. They are never dropped and never behind an upsell.** The card says "Will read this tomorrow."
  - Sensitive and local items are unaffected.
  - This avoids complaints 4 and 8: no paywall on core function and no stalled processing.

**Pro tier**, mapped to the post-beta queue:

| Pro feature | Post-beta queue item |
|---|---|
| Backlog sweep / graveyard report, with fair batching and no hard daily cap (#5). Free users get a one-time taste of their newest 100. | #5 |
| Purchases and return tracker, slice 1 + 2 (#1) | #1 |
| Expense CSV export (#1) | #1 |
| Search by meaning (#7) | #7 |
| 100 extractions/day (the existing COMP-QUOTA constant) | — |
| Image escalation on auto-detected items by default | — |

Teach-by-correction (#3) and source highlighting (#2) **stay free**. They are trust features, and charging for trust contradicts F7.

**Prices.** Pro is **$3.99/month or $24.99/year**. That sits mid-market: SnapReminder $4.99/$39.99, Captureist $2.49/$12.99, Snap2Plan €1.99 (listings).
- **Trial:** 7-day free trial on the annual plan only, through Apple and Google intro offers.
- **Student:** $14.99/year through **offer codes** handed out on campus and in student orgs. The stores have no student verification, and third-party verifiers cost money and collect PII.

**Alternatives and why they lose:**
- **One-time unlock ($14.99):** proceeds of ~$12.70 cover the typical cost for years. But it does not fund the recurring work: the server, ~2–4 h/month of policy-table upkeep (analyst §2), and model price changes. Keep it as a possible **lifetime option ($49.99)** later if F8 shows subscription aversion.
- **Credits / consumables:** usage anxiety makes users ration screenshots, which defeats the loop. Credits also bring store rules on credit expiry and restore. Rejected.
- **Free + tip jar:** cannot reach break-even past ~1k MAU. Fine for the beta only.
- Ads and data sales are excluded by the positioning.

## 4. Break-even sketch (all inputs are **assumptions**)

Assumptions:
- Cost: $0.08 variable per MAU, plus fixed costs (Apple $99/yr, host $15→$50→$600/mo, observability ~$200/mo at 100k).
- Payers split 60% annual / 40% monthly. Blended gross is $2.85/payer-month; **net after 15% is $2.42**.

| MAU | Monthly cost | Revenue at 3% conversion | Revenue at 5% conversion | Break-even conversion |
|---|---|---|---|---|
| 1k | ~$105 | $73 | $121 | **~4.3%** |
| 10k | ~$880 | $726 | $1,210 | **~3.6%** |
| 100k | ~$8.9k | $7.3k (–1% RevenueCat) | $12.1k | **~3.7%** |

Freemium conversion of 2–5% is a common rule of thumb (*unverified*), so **the model is marginal**. Levers, in order of impact:
1. Measure the real screenshot rate. 20/day is a deliberately high load-planning figure, and at 10/day the cost per MAU roughly halves.
2. Run free-tier catch-up and queued items (not live shares) through the Batch API, at about 50% of the cost (*verify the batch discount*).
3. Keep escalation at or below 10%.
4. Price is the last lever.

## 5. Beta instrumentation and a fake-door test

F8 additions. All are **enum or count only, with no user_id and no free text**, so the EVAL-BAR-14 scan still applies:
- `pro_door_event`: `view | tap_feature | dismiss`, with `pro_feature`: `backlog_sweep | purchases | expense_export | semantic_search | higher_limit | none`.
- `wtp_bucket` (single-choice, optional): `0 | lt1 | 1_2 | 2_4 | 4_6 | gt6` (USD/month).
- `plan_pref`: `monthly | annual | lifetime | none`.
- `shadow_cap_hit`: a server count of calls that *would* exceed 30/day. It is aggregated, and the token is not stored in the metric table.
- `import_cap_hit`: the 20-item import cap was reached (signals backlog demand).
- `usage_day_bucket`: a device-local daily histogram `0 | 1_5 | 6_15 | 16_30 | 31+`, uploaded as counts.
- `search_zero_result`: count only.

**Fake door.** Settings gets a row, "Pro (not available in beta)". It lists the five features with an "I'd use this" tap and the optional price question. The disclosure is shown on the screen:

> "Nothing is for sale during the beta. Taps are counted anonymously to decide what stays free. Everything you use today stays free."

There is no IAP code and no purchase button, so nothing is bait-and-switch. This should also be added to the tester consent note.

## 6. Risks

- **Subscription fatigue.** Mitigation: a generous free core, an annual plan priced near one month of a competitor, and a lifetime fallback.
- **Platform fee changes.** Google restructured in 2026, and Apple's US link-out fee is pending. Keep the price model fee-agnostic, so neither depends on US web checkout.
- **LLM price spike or deprecation.** Pro carries 10–30× margin over the cost of a typical user. A model swap goes through the eval gate. EVAL-COST-01 stays a ship bar.
- **Refunds.** Apple decides refunds, and the developer cannot refuse them. Google lets the developer refund, and the EU has a 14-day withdrawal right (*verify*). Use server-side entitlement checks so a refunded subscription revokes Pro.
- **App Store guidelines.**
  - 3.1.2(a): a subscription must give "ongoing value". Ongoing server cost and new features justify it.
  - 3.1.2(c): state what Pro includes before asking anyone to subscribe.
  - 3.1.1: unlocks must use IAP; no license keys.
  - 5.1.2(i): explicit consent before sharing with third-party AI. Already designed into F7 and onboarding.
  - Source: [guidelines](https://developer.apple.com/app-store/review/guidelines/), fetched.
- **The $25 provider cap.** It is a global hard stop. Forecast spend at 1k MAU is ~$80/month, so once anyone pays, a free-tier spike could cut off paying users. Before public launch:
  1. Raise the cap to about 2× forecast.
  2. Split COMP-QUOTA's global daily $ budget by tier.
  3. Have the free tier go into "queue until tomorrow" first, while Pro keeps processing.

  For the beta, $25 is fine: 50 testers × $0.40 worst case = $20.

## 7. Decide now vs after the beta

**Now (before the Nov 25 CP0 contracts freeze), all additive:**
- Token record: `tier` enum `beta | free | pro`, default `beta`. It is never trusted from the client.
- `/v1/extract` response: optional `quota: {tier, state: ok | near | exhausted}`. The existing `503 {basic:true}` stays for the kill switch and cap.
- `metric_daily` dimensions: the F8 enums in §5, plus a `cap_tier` enum on cap events.
- COMP-QUOTA: a per-tier limit table read from `worker_config`. Beta: 100/day, with a 30/day shadow threshold.
- Policy decisions:
  - No ads, no data sales.
  - The core loop stays free. Tell testers this in writing.
  - No IAP in the beta.
  - Enroll in Apple's Small Business Program at account setup.

**After the beta, using F8 data:**
- Free cap number (30 vs 20 vs 50).
- Prices and student price.
- Whether to add a lifetime option.
- Which features go into Pro.
- RevenueCat vs direct StoreKit/Billing (needs an Expo dev build either way).
- Batch API for queued free items.
- Raising and splitting the provider cap.
