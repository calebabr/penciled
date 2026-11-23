# 1a. Screenshot behavior: what people screenshot and why

Caveat up front: no large, rigorous, category-ranked screenshot survey was found. The best academic source (Mottelson, DIS 2023) could not be opened (ACM returned 403; the abstract page is empty), so its category data is not quoted here. The ranking below is therefore an ESTIMATE built from small surveys, vendor content, and qualitative threads. Treat it as a hypothesis to validate with in-app data.

## Sources actually read or surfaced

| # | Source | What it gives | Quality |
|---|---|---|---|
| S1 | [Screenshot Habits (GitHub, saraclay)](https://www.github.com/saraclay/Screenshot-Habits) | n=55 smartphone users. 21% screenshot several times a day, 45% several times a week, 27% occasionally, 5% rarely. Multi-select categories: funny memes/images 38, articles/e-books 24, receipts/bills 22, food/recipes 22, clothes/fashion 13, wishlist items 12. Qualitative: "I never delete them, they clog my memory." | Tiny, informal sample; the only category counts found |
| S2 | [Smallpdf, "Screenshotted to Death"](https://smallpdf.com/blog/screenshotted-to-death) | Per search-tool summary (page body would not load for me): Americans keep about 430 screenshots, take about 5/day, most often capture recipes, emails, travel details. Sample size not stated. | Vendor marketing; unverified, low confidence |
| S3 | [Mottelson, "Why do people take Screenshots on their Smartphones?", DIS 2023](https://hcds.itu.dk/bibliography/mottelson2023b.html) (DOI 10.1145/3563657.3596067) | Per search-tool summary only: survey of 306 people; cognitive offloading ("remember something") motivated 30.6% of screenshots vs 19.2% of photographs. Not verified against the paper. | Peer-reviewed, but secondhand here |
| S4 | [JCMC 2024 article on screenshots of messages](https://dbpia.nl.go.kr/jcmc/article/30/1/zmae023/7978203) | Screenshots act as socialization tools; youth send message screenshots to friends for advice; sharing norms shape the tendency. | Academic, secondhand |
| S5 | [Binghamton study via ConsumerAffairs](https://www.consumeraffairs.com/news/screenshots-are-supposed-to-help-you-remember-a-study-found-the-opposite-082626.html) | Students remembered less about info they screenshotted than info they only viewed. Narrow student sample; did not test deliberate revisiting. (Page returned 403 for me; summarized from search snippet.) | Lab study, narrow |
| S6 | [Public Storage, "Avoiding the Screenshot Graveyard"](https://www.publicstorage.com/blog/public-storage/avoiding-the-screenshot-graveyard-how-to-find-information-you-keep-saving.html) | No statistics (read in full). Lists recurring types: products to buy, recipes, travel recommendations, articles/tutorials, quotes. Problem types: event flyers (need calendar entry), recipe carousels, account/confirmation details. Temporary items to delete after use: directions, parking, shipping updates, one-time codes. Advice: weekly Act / Save / Delete triage. | Advice article; useful taxonomy only |
| S7 | [Product Hunt thread, "10k screenshots you never check"](https://www.producthunt.com/p/unbury/do-you-have-10k-screenshots-that-you-took-to-remind-yourself-yet-u-never-check-them) | Poster reports thousands of screenshots of posts, articles, products taken as reminders, mostly never acted on. | Anecdote; founder promoting a product |
| S8 | [r/ADHD "ADHD and screenshots" (Dec 2024 mirror)](https://lr.us.psf.lt/r/ADHD/comments/1hnn7pf/adhd_and_screenshots/m4303du/?context=3) and [2021 thread](https://axebps-redlib.hf.space/r/ADHD/comments/motdce/i_have_this_habit_of_saving_posts_and_screenshots) | Qualitative: save "just in case," rarely reopen. Targets named: recipes, job postings, error messages, articles, products, old chats. One commenter finds recipes later only via photo-app search. | Anecdote; ADHD community skews the sample |
| S9 | [input.sh, "Screenshots as a layer of interoperability"](https://input.sh/screenshots-as-a-layer-of-interoperability) | Argues screenshots work as a universal workaround for apps that do not interoperate; capture matters more than retrieval ("security blanket"). | Commentary |
| S10 | [Popsa survey via Dead Pixels Society](https://thedeadpixelssociety.com/popsa-research-reveals-most-smartphone-photos-are-never-revisited/) | n=8,000 (as reported); 70% of photos never revisited; half say camera roll stresses them. About photos generally, not screenshots; use only as a proxy for the graveyard effect. | Vendor survey, proxy |
| S11 | [The Conversation, "I studied 5,000 phone images"](https://theconversation.com/i-studied-5-000-phone-images-objects-were-more-popular-than-people-but-women-took-way-more-selfies-150080) | Phone-image study with an "evidence and receipts" category; mentions screenshotting influencer looks to copy. Photos generally, not screenshots only. | Academic author, proxy |

## Volume (what the evidence supports)
- Frequency: weekly-or-more is the norm in the only survey found (S1: 66% at least several times a week; n=55, so an estimate at best).
- Rough scale claims: about 5/day and about 430 stored (S2, vendor, unverified). ESTIMATE for design: a typical user accumulates hundreds, a heavy user thousands (S7, S8 anecdotes).
- Graveyard evidence is consistent but mostly qualitative: nobody deletes, nobody revisits (S1, S6, S7, S8, S10).

## Why people screenshot
1. Offload memory / "deal with later" (S3: ~31% of screenshots, self-report, unverified here).
2. Work around apps that cannot save, share, or export a thing (S9, S4).
3. Social sharing and asking for advice, especially message threads (S4).
4. Shopping intent: see item, screenshot instead of clicking (search-result summary of commentary; no primary source verified).

## Ranked categories (ESTIMATE, my synthesis; not measured)
Commonness score from S1 counts plus mentions across S2, S6, S7, S8. Action score is my judgment of how often a follow-up is implied.

| Rank | Category | Commonness (est.) | Follow-up implied (est.) | Typical one-tap action |
|---|---|---|---|---|
| 1 | Events / flyers / invites / schedules (school and work info included) | Medium (not in S1; named in S6; likely high for students) | Very high (almost always) | Add to calendar with date, time, place, reminder |
| 2 | Receipts, bills, order and booking confirmations, codes | High (S1: 22/55) | High | Extract amount/vendor to expense or reminder; track package; set return deadline; store code with expiry |
| 3 | Shopping: products, wishlist, fashion | High (S1: 13 + 12) | High | Find product and price, add to wishlist, alert on drop |
| 4 | Recipes / food posts | High (S1: 22; S2, S6, S8 all name it) | Medium-high (intent to cook) | Extract ingredients and steps, grocery list, save to recipe box |
| 5 | Travel: places, itineraries, tips | Medium (S2, S6) | Medium-high | Pin places on a map list, build trip note |
| 6 | Messages / chats / social posts (advice, proof, info) | Likely very high but unmeasured (S4, S8; absent from S1 list) | Medium (answer, share, remember a detail, extract phone/address) | Extract contact, address, date; reply or share |
| 7 | Articles, tutorials, job postings, school/work reference | Medium-high (S1: 24) | Medium (read later, apply) | Resolve link to read-later; deadline to reminder |
| 8 | Memes / funny images | Highest single count in S1 (38/55) | Low (share or keep) | Share, tag, auto-archive |

Ranking logic: opportunity for a "one-tap action" product is commonness times follow-up probability, so events, receipts/confirmations, shopping, and recipes lead. Memes are the most common but need almost no action, so they should be auto-filed out of the way rather than prompted. Messages are probably underrepresented in S1; validate before ranking.

## Implications for design (hypotheses)
- Time-bound items (events, deadlines, codes, shipping) decay quickly, so surfacing them early has the highest value; the Public Storage "delete after use" list (S6) implies auto-expiry.
- Capture is the satisfying step; retrieval is the failure (S9, S7). An action at capture time or soon after beats a search UI.
- Sensitive content (account details, receipts) is common (S6), so on-device processing is a likely trust requirement.

## Gaps to close
- Open Mottelson (DOI above) for the real category and purpose breakdown.
- Find platform data (Google Photos or Apple) on screenshot share of library; none found in this pass.
- Search found no rigorous quantification of the share of screenshots ever revisited; the 70% figure (S10) is for photos generally.
