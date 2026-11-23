# 1a — Candidate Features (Feature Ideator)

Design-only. Every action follows one loop: **model reads and proposes, deterministic code validates and executes, user confirms, and extracted fields stay editable.** "Magic" means the app seems to know what you meant. "Useful" means it does the job but still makes you do the thinking.

---

## Capture (how screenshots get in)

**1. Auto-watch new screenshots (on-device)**
- *Value:* Every screenshot is processed in the background, so there is nothing to remember to do.
- *Magic vs useful:* Useful means a list of processed images. Magic means a quiet notification seconds later, like "Looks like a concert on Dec 6. Add to calendar?", before you have left the app you screenshotted.

**2. Share-sheet "Act on this"**
- *Value:* Send any image, photo, or PDF page to the app from anywhere, including images that aren't screenshots.
- *Magic vs useful:* Useful means it imports the file. Magic means the share sheet itself shows the proposed action card, so you confirm without ever opening the app.

**3. Backlog sweep with a "graveyard" report**
- *Value:* On first run, scan the last N months of screenshots so the app is useful on day one.
- *Magic vs useful:* Useful means everything gets indexed. Magic means a short, slightly embarrassing summary, like "You have 14 recipes, 6 expired events, and 3 receipts you never logged", with a one-tap batch triage.

**4. Burst / scroll stitching**
- *Value:* Several screenshots taken in a row (a long chat, a multi-part recipe) are grouped and understood as one item.
- *Magic vs useful:* Useful means they are grouped by timestamp. Magic means the full ingredient list is extracted even though it was split across three images.

## Understanding

**5. Classify + extract with confidence flags**
- *Value:* Each screenshot gets a type (event, deadline, receipt, recipe, link, other) and structured fields.
- *Magic vs useful:* Useful means correct fields. Magic means the app is honest about uncertainty: shaky fields are highlighted ("year unclear, assumed 2027"), so you check one thing instead of everything.

**6. Context-aware resolution**
- *Value:* Turns relative or partial details into concrete ones, like "this Friday" into a date, "the usual place" into nothing (flagged), or a venue name into an address.
- *Magic vs useful:* Useful means parsing explicit dates. Magic means resolving "tmrw 7" against when the screenshot was taken, not when you open it. Deterministic date logic does the resolving; the model only flags the phrase.

**7. Multi-intent screenshots**
- *Value:* One screenshot can produce more than one action, like a flyer that gives both an event and a "buy tickets by Nov 30" reminder.
- *Magic vs useful:* Useful means one best guess. Magic means it catches the secondary deadline you would have missed.

**8. Junk / "just a memory" detection**
- *Value:* Memes, photos of friends, and game scores are recognized as not actionable and stay out of your way.
- *Magic vs useful:* Useful means fewer false prompts. Magic means the app learns your personal noise patterns, like never proposing anything for your Wordle shares.

## Actions

**9. One-tap action cards (the core five)**
- *Value:* Calendar event, reminder, expense entry, grocery list, and saved link with summary, each written through the native OS API after you confirm.
- *Magic vs useful:* Useful means a form. Magic means the form arrives pre-filled and correct about 90% of the time, so confirming takes one tap and editing is a single field tap.

**10. Smart grocery merge**
- *Value:* Recipe ingredients are merged into one existing list with quantities combined and pantry staples deduplicated.
- *Magic vs useful:* Useful means items get appended. Magic means "2 cups flour + 1 cup flour = 3 cups flour" across two recipes, with an "already have?" toggle for staples.

**11. Deadline ladders**
- *Value:* A deadline gets sensible lead-time reminders (for example 3 days, 1 day, and the morning of) rather than one alert.
- *Magic vs useful:* Useful means one reminder. Magic means the lead time scales with the task: a scholarship essay gets a week, an RSVP gets a day. The defaults are deterministic rules, and you can see and edit them.

**12. Expense export**
- *Value:* Receipts become rows (merchant, date, total, category) that export to CSV or a spreadsheet.
- *Magic vs useful:* Useful means a list. Magic means a monthly "you screenshotted $214 of receipts" summary, plus a split-with-friends total from a group-chat receipt.

## Retrieval

**13. Search by meaning (on-device embeddings)**
- *Value:* Find "that ramen place someone sent me" or "the blue jacket" without remembering words or dates.
- *Magic vs useful:* Useful means OCR keyword search. Magic means fuzzy, half-remembered queries work, and results show the extracted card, not just the image.

**14. Auto-collections**
- *Value:* Screenshots group themselves into living collections like Recipes, Trip to Atlanta, Gift ideas, and Apartments.
- *Magic vs useful:* Useful means folders by type. Magic means topic clusters you never created ("Looks like you're planning a trip to Atlanta — 7 items"), which you can rename, merge, or dismiss.

**15. Timely resurfacing**
- *Value:* Saved items come back when they become relevant, like the restaurant on a Friday evening, the gift idea two weeks before a birthday on your calendar, or an unused coupon before it expires.
- *Magic vs useful:* Useful means a weekly digest. Magic means a single well-timed nudge that makes you think "oh right, I wanted that." It needs strict rate limits so it never becomes spam.

**16. "Still want this?" decay review**
- *Value:* A periodic swipe review of unacted items: act, keep, or let go (and optionally delete the original screenshot).
- *Magic vs useful:* Useful means bulk delete. Magic means the camera roll actually gets lighter, and the app shows reclaimed storage and "intentions completed" as a quiet win.

## Trust / control

**17. Editable proposal with source highlighting**
- *Value:* Every field in a proposed action can be edited, and tapping a field highlights the exact region of the screenshot it came from.
- *Magic vs useful:* Useful means editable text boxes. Magic means visible provenance: you can see why it thinks the event is at 8pm, which builds trust fast.

**18. Undo everything + action log**
- *Value:* Every executed action is logged and can be reversed (delete the event, remove the reminder) from one place.
- *Magic vs useful:* Useful means a history list. Magic means confidence: one-tap confirm feels safe because one-tap undo exists, including a 10-second "undo" snackbar.

**19. Privacy mode indicator + sensitive-content guard**
- *Value:* A clear badge shows whether processing happened on-device or in the cloud. Screenshots that look like banking, passwords, IDs, or medical info are never sent off-device and can be auto-excluded.
- *Magic vs useful:* Useful means a settings toggle. Magic means the app proactively says "This looks like a bank screen; I skipped it", so it feels like it is on your side.

**20. Teach-by-correction**
- *Value:* Your edits become local preferences, like your default calendar, how you categorize expenses, or "Target = Groceries."
- *Magic vs useful:* Useful means remembered defaults. Magic means proposals visibly improve week over week. These are stored as explicit, viewable rules, not hidden model fine-tuning, which keeps them deterministic and auditable.

---

## Ideator's note on scope

For a mid-January beta, the likely minimum set is features 1/2, 5, 6, 9 (calendar and reminder first), 13, 17, 18, and 19. Features 3, 14, and 15 carry the most "magic" per unit of effort once the core loop is trustworthy. Features 4, 7, 10, and 20 are strong v1.1 candidates.
