# Purchase action: feature research (analyst 1)

Date: 2026-11-19. Method: web search + page reads only. Labels: [V] verified on an official/primary page, [S] secondary source, [?] unconfirmed. Most competitor facts are vendor self-description.

## 1. Competitors and complaints
- Named products (HomeBase, HousePulse, Sustain) returned nothing in search [?]; HomeTally and RecallSentry appear only via listings. HomeTally markets "insurance-ready reports" with photos, values and warranty status; RecallSentry monitors four federal agencies and alerts on household-inventory matches [S] ([ConsumerAffairs](https://www.consumeraffairs.com/news/new-app-alerts-you-when-theres-a-recall-031626.html), [HomeTally/ClaimProof/Stuffolio results](https://apps.apple.com/app/claimsready/id6758244506)).
- Wide field of tiny App Store apps all promise "receipt scan -> return window + warranty reminder": [Covered](https://apps.apple.com/us/app/id6761128957), [Kept](https://appshunter.io/ios/app/kept-warranty-and-receipts/id6775344341), [Return Radar](https://apps.apple.com/ph/app/return-radar/id6761351819), [PARS Follow AI](https://apps.apple.com/app/id6823419784) (reads Gmail/Outlook/IMAP). WarrantyVault: free for 5 products, Pro for unlimited + iCloud sync, too few ratings to judge ([listing](https://apps.apple.com/us/app/id6758866183)).
- Recall add-ons exist but are gated: CoverKeep scans against CPSC data; daily automatic recall alerts are paid [S] ([listing](https://apps.apple.com/app/id6764136941)).
- Return deadlines are AI-estimated: Receipt Return says so explicitly ([listing](https://apps.apple.com/tr/app/receiptreturn/id6761314944)). Privacy positioning (no account, on-device) is a differentiator: [ReturnMinder](https://apps.apple.com/us/app/returnminder/id6760627062), [Receipt Roost](https://mwm.ai/apps/receipt-roost/6770024318).
- Platform incumbents: Apple Wallet order tracking parses Mail-app emails only (not Gmail), needs Apple Intelligence, no merchant list, some orders never complete because merchants omit "delivered" emails [V] ([Apple](https://support.apple.com/en-gb/guide/business/abcbb713dd73/web)). Gmail purchase cards, Shop app, Paribus-style tools: not verified in search [?]. None found tracking return deadlines; unconfirmed.
- Complaints: I found NO retrievable review text or Reddit threads on missed deadlines or OCR errors [?]. Inferred, not evidenced: wrong dates, paywalls on recall alerts, manual-entry burden, stale apps (one 2013-era Android tracker reported dead, [ghacks](https://www.ghacks.net/2013/11/17/warranty-tracker-android-keeps-track-warranties-deadlines/)). Recommend a follow-up review-mining pass.

## 2. Retailer return policies
**No structured public source or API found; a hand-curated table is required [S, absence of evidence].** Policies live in prose on each retailer's page and change seasonally.

Real variance (verify against each retailer page before shipping; sources below are secondary unless noted):
- Amazon: 30 days from delivery, exceptions (computers/Kindle); holiday gift window to Jan 31 ([Amazon](https://digprjsurvey.amazon.com/csad/help/node/GKM69DUUYKQWKWX7), [MoneyTalks](https://www.moneytalksnews.com/amazon-gives-you-until-jan-to-return-gifts-return-traps-still-catch-shoppers/)).
- Walmart: ~90 days general; electronics 30 days, phones 14 [S]; holiday extension to Jan 31 per a mirror site [?] ([ConsumerAffairs holiday](https://www.consumeraffairs.com/news/the-2025-holiday-returns-playbook-heres-what-new-and-how-to-protect-your-refund-122225.html), [Walmart overview](https://www.gobankingrates.com/saving-money/shopping/walmart-return-policy-warranty/)).
- Target: 90 days most items, +30 for Circle Card, electronics 30 days, Apple shorter (14 vs 15 days conflict), own-brand up to 1 year; 2025 electronics holiday window to Jan 24, Apple/Beats excluded ([Target](https://www.target.com/returns), [MoneyTalks](https://www.moneytalksnews.com/retailers-with-extended-policies-for-the-holiday-season/)).
- Best Buy: holiday window (purchases Oct 31-Dec 31 returnable through Jan 15, 2026), activatable devices 14 days, restocking fees 15% opened electronics reported [S] (dates conflicted across sources) ([Priceva](https://priceva.com/blog/best-buy-return-policy)).
- Costco: 90 days electronics from receipt; most else no fixed limit ([SlashGear](https://www.slashgear.com/1678320/costco-electronics-return-policy-explained)).
- Apple 14 days (varies by source); H&M 30 days; Zara/Nike windows [?] unconfirmed; Zara charges return fees up to $8.50 per one roundup ([Kiplinger](https://kiplinger.com/personal-finance/shopping/601777/holiday-return-policies-at-32-leading-retailers), [KCL](https://thekrazycouponlady.com/tips/money/stores-doing-returns)).
- Axes the schema must carry: start anchor (delivery vs order/purchase vs ship date), category override (electronics/phones/clothing/own-brand), membership bonus, holiday override (date range -> fixed end date), fees (restocking %, return shipping), marketplace sellers (third-party Amazon/Walmart items follow seller policy, [?]).

**Effort estimate (my judgment, [?]):** top ~25 US retailers x ~3 category rules ~ 75-100 rules. Initial research + verification ~3-5 days; ongoing upkeep ~2-4 hrs/month, plus a 1-2 day sprint each October for holiday overrides (~10 of the 25 publish them). Mitigation: show date as "estimated", let user edit, fall back to a default (30 days) with a "check store policy" link, record `policy_version` and `last_verified`.

## 3. Recall sources
| Source | Access | Notes |
|---|---|---|
| CPSC | REST `https://www.saferproducts.gov/RestWebServices/Recall`, `format=json`, filters Title/RecallDescription/ProductName (and date params) | [V] [CPSC API page](https://www.cpsc.gov/Recalls/CPSC-Recalls-Application-Program-Interface-API-Information). Terms, update frequency, rate limits NOT stated on page [?]. Fields observed live: RecallID, RecallNumber, RecallDate, Title, Description, Products, Manufacturers, Retailers, SoldAtLabel, **ProductUPCs**, Hazards, Remedies. In sampled records ProductUPCs and Products.Model were empty; model/UPC usually only in free-text Description (e.g. "model number GTF7530, and UPC Code ...") ([live query](https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallDateStart=2026-10-01)). |
| NHTSA | `api.nhtsa.gov/recalls/recallsByVehicle` (make/model/year), campaign lookup; bulk flat files | [S] ([guide](https://www.carwhere.com/guides/vehicle-recall-api), [Data.gov](https://catalog.data.gov/dataset/nhtsas-office-of-defects-investigation-odi-recalls-nhtsa-api)). Vehicle/VIN-based, not UPC; off-scope for screenshots. Official docs not retrieved. |
| FDA | openFDA `api.fda.gov/{food,drug,device}/enforcement.json` | Key page: 240 req/min, 120k/day with key; keyless limits conflict across sources ([openFDA](https://open.fda.gov/apis/authentication)) [V/S]. Food/drug/device mostly; free-text product descriptions, UPC sometimes inside text [?]. |
| USDA FSIS | JSON GET API `fsis/api/recall/v/1`, no auth reported | [PDF docs](https://www.fsis.usda.gov/sites/default/files/media_file/documents/Recall-API-documentation.pdf), [press](https://www.fsis.usda.gov/news-events/news-press-releases/fsis-launches-new-recall-and-public-health-alert-api). Meat/poultry/egg; food rarely a "purchase screenshot" case. |
| Health Canada | not researched [?] | |
| EU Safety Gate | public JSON behind portal reported by scrapers; no official API docs found [?] | [example listing](https://api.store/eu-institutions-api/directorate-general-for-justice-and-consumers-api/safety-gate-the-eu-rapid-alert-system-non-food-api). Verify terms before use. |

**Matching implication:** because structured UPC/model is sparse, recall matching must be fuzzy (brand + product name + model string extracted from the receipt vs Title/Description/Retailers), ship as "possible match, confirm", and never as "safe". Receipts rarely carry UPC; model numbers appear only for some electronics. Expect low recall-precision, so plan to fetch a local mirror (daily sync of the CPSC feed) rather than per-item live queries (and confirm CPSC terms/limits).

## 4. Warranty
- No structured source of manufacturer standard terms found; terms live in per-product docs [?]. Practical approach: small curated brand/category defaults (e.g. electronics 1 year) labeled "typical", user-editable, plus credit-card extended-warranty as manual note.
- US: Magnuson-Moss does not require any written warranty; it governs disclosure and prohibits deceptive terms ([FTC statute page](https://ftc.gov/legal-library/browse/statutes/magnuson-moss-warranty-federal-trade-commission-improvements-act), [summary](https://lemberglaw.com/the-magnuson-moss-warranty-act)). So no universal US minimum to default to; implied warranties are state-law.
- EU: 2-year legal guarantee for goods (Directive 2019/771) and 14-day withdrawal for distance sales (Consumer Rights Directive); my search did not retrieve primary text, so [?] cite from EUR-Lex before use. Out of US-first scope; just keep `jurisdiction` field.

## Takeaways for design
1. Differentiator is passive capture + honest "estimated" dates, not another scanner; crowded, low-trust category.
2. Return deadline = curated rules table + user-editable; store anchor type and `last_verified`.
3. Recall = fuzzy local-mirror matching with "possible match" UX; do not promise coverage.
4. Gaps in this research: no real user reviews, Reddit, Health Canada, Shop/Gmail/Paribus, Nike/Zara policies, official EU text.
