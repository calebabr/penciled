# 1a. Competitor / Platform Feature Analysis (research date 2026-11-18)

Method note: web search + page reads only. App Store feature claims are developer-written and unverified. Most small apps have 0-3 ratings, so review evidence is thin. I could not retrieve any Reddit thread directly; Reddit-sourced claims are marked unverified. Android third-party options surfaced were few (Shots Studio). Gaps are flagged rather than filled.

## 1. Platform features

**Apple iOS 26 screenshot + Visual Intelligence.** Screenshot UI gains three buttons: Add to Calendar (extracts event details, fills an entry, user taps to confirm), Image Search, and Ask (ChatGPT) ([9to5Mac](https://9to5mac.com/2025/07/15/iphone-screenshots-are-getting-three-powerful-new-features-in-ios-26/)). It produces an editable draft event ([iDropNews](https://www.idropnews.com/?p=256322)). Needs an Apple Intelligence device (iPhone 15 Pro or newer per [TechRadar roundup](https://www.techradar.com/phones/ios/im-a-serial-iphone-screen-shotter-and-i-cant-wait-to-use-these-3-new-features-when-ios-26-launches)). Third-party calendar support is reported inconsistently ([Tom's Guide](https://www.tomsguide.com/phones/iphones/how-to-use-visual-intelligence-on-iphone-to-make-calendar-events) vs [9to5Mac](https://9to5mac.com/2026/03/05/ios-26-gives-apples-calendar-app-a-convenient-new-advantage/); I could not read either body). Calendar only: no reminder, expense, grocery or summary actions found.

**Google Pixel Screenshots (Pixel 9/10).** Summarizes and analyzes screenshots, offers filtering, link extraction, reminders, and AI search ([Android Authority](https://www.androidauthority.com/google-made-me-turn-off-pixel-screenshots-3680197/)). Reviewers call it "imperfect but surprisingly helpful" ([MobileSyrup](https://mobilesyrup.com/2024/08/21/pixel-screenshots-hands-on/), via search snippet). As of June 2026 part of processing moved to the cloud ([9to5Google](https://9to5google.com/2026/06/17/pixel-screenshots-cloud-ai/)). Daily processing throttle (about 300 images in one tester's run), per [search summary of Android Authority review](https://www.androidauthority.com/pixel-screenshots-review-3476772) (page returned 403 to me; treat as secondary).

**Pixel Magic Cue.** Proactive suggestions; "excellent but only when it noticeably worked," rarely appears, limited regions ([9to5Google](https://9to5google.com/2025/09/06/i-like-the-pixel-10-in-spite-of-googles-ai-not-because-of-it/), [poll](https://9to5google.com/2025/11/18/poll-do-you-notice-google-pixels-magic-cue/)).

**Google Circle to Search.** Manual gesture search over on-screen content; it is a search tool, not an action tool. Requires Google as default assistant ([Android Authority](https://www.androidauthority.com/circle-to-search-default-search-engine-teardown-3416769)); Share button removed in 2026 ([Android Authority](https://androidauthority.com/circle-to-search-missing-share-button-3638368), [PiunikaWeb](https://piunikaweb.com/2026/02/13/google-circle-to-search-share-button-removal-is-working-as-intended/)); reported breakage on Galaxy S24 Ultra ([SamMobile](https://sammobile.com/news/circle-to-search-broken-on-the-galaxy-s24-ultra-for-some-users)).

**Samsung Galaxy AI / Now Brief.** Now Brief is a proactive daily card; reviewers found it shallow (weather, calendar, news) and inconsistent ([Android Authority](https://www.androidauthority.com/now-brief-needs-to-be-good-not-ai-3619962/), [Gizmodo](https://gizmodo.com/s25-most-underwhelming-feature-2000555965)). Samsung offers a system-wide toggle for cloud AI, which a reviewer praised as the model Google should follow ([Android Authority](https://www.androidauthority.com/google-made-me-turn-off-pixel-screenshots-3680197/)). I found no source documenting a Samsung screenshot-to-calendar flow; unverified gap.

## 2. Third-party apps

| App | Platform | Auto vs manual | Actions | Pricing / rating (from listing) |
|---|---|---|---|---|
| [SnapReminder](https://apps.apple.com/us/app/id6758023554) | iOS | Manual share-sheet; OCR+AI extracts dates/amounts | Reminders, optional calendar sync, voice reschedule | Free; Pro $4.99/mo or $39.99/yr; no ratings yet |
| [ScreenshotAI: Calendar Events](https://apps.apple.com/app/id6758288223) | iOS | Share sheet or camera, confirm in one tap | Calendar, Reminders, Maps | Not verified |
| [Snap2Plan](https://apps.apple.com/us/app/id6754525197) (per search summary) | iOS | Manual | Calendar, Reminders | Free 25 AI queries; Pro EUR1.99/mo (search summary, not opened) |
| [Captureist](https://apps.apple.com/us/app/captureist/id6443865506) | iOS/Mac/visionOS | Auto recognition of phones, links, dates, addresses | Call, open Maps/Safari, create calendar event; text search; folders | Free; $2.49/mo, $12.99/yr; 4.7 from 3 ratings |
| [Shotted](https://www.producthunt.com/products/shotted/alternatives) | iOS | Imports screenshots; instant summaries | Reminders, event details, categories, cleanup | Not stated; claims on-device |
| [SnapSort](https://apps.apple.com/app/id6746203579) | iOS | Auto categorization (chats, receipts, memes) | Folders, search (in-image text search "coming soon") | $2.99 one-time Pro; 1.0 from 2 ratings |
| [ShotSweep](https://apps.apple.com/app/id6758150150) / [ScreenSift](https://apps.apple.com/us/app/-/id6755496303) | iOS | Cleanup focus | Delete duplicates; subscription-gated | Via [search results](https://apps.apple.com/app/id6758150150) |
| [Shots Studio](https://maketecheasier.com/shots-studio-organize-android-screenshots) | Android, open source | Auto tag/collections via AI scan; user must run scans | Collections by text description, tags, reminders to resurface | Free; needs own Gemini API key or slow local Gemma |
| Pool, Clutter, Captr, Tote ([vendor blog](https://nemos-landing.pages.dev/blog/best-screenshot-organizer-apps-iphone), written by a competitor, no hands-on testing) | iOS | Clutter manual; Captr/Tote extract | Captr: calendar/reminders; Tote: searchable saves of Reels/links | Not listed |

Observed category pattern: calendar and reminder are the only action types any competitor ships. I found no app offering receipt-to-expense, recipe-to-grocery, or chat-deadline-to-reminder as named flows. That is an absence-of-evidence finding from limited search, not proof.

UX strengths seen: one-tap confirm (Apple, ScreenshotAI), share-sheet entry (SnapReminder), per-type quick actions (Captureist). Weaknesses: manual entry points, draft-only output, tiny single-purpose scope.

## 3. Ten most common complaints (evidence strength noted)

1. **Silent privacy change / cloud processing of sensitive screenshots.** Pixel Screenshots moved to cloud without in-app notice ([Android Authority](https://www.androidauthority.com/google-made-me-turn-off-pixel-screenshots-3680197/), [9to5Google](https://9to5google.com/2026/06/17/pixel-screenshots-cloud-ai/)).
2. **Cloud AI and API key friction on Android.** Shots Studio free Gemini cap (about 80 images/day) and a privacy tradeoff ([MakeTechEasier](https://maketecheasier.com/shots-studio-organize-android-screenshots)).
3. **Local models are slow and drain battery.** Gemma overheating, battery drain, GPU crashes (same source).
4. **Throttled or stalled processing of backlog.** Pixel Screenshots daily limit ([Android Authority review](https://www.androidauthority.com/pixel-screenshots-review-3476772), secondary).
5. **Proactive features are rare or unhelpful.** Magic Cue and Now Brief ([9to5Google poll](https://9to5google.com/2025/11/18/poll-do-you-notice-google-pixels-magic-cue/), [Android Authority](https://www.androidauthority.com/now-brief-needs-to-be-good-not-ai-3619962/)).
6. **Failure to detect or import screenshots; paid upgrade did not help.** SnapSort reviewer requested a refund ([App Store](https://apps.apple.com/app/id6746203579)).
7. **Reliability bugs in reminders/notifications and purchase restore.** SnapReminder's own release notes admit lost notifications and broken restore ([App Store](https://apps.apple.com/us/app/id6758023554)).
8. **Paywalls and subscription gating of core function.** Many cleaners and AI apps gate deletion or scans ([search results](https://apps.apple.com/app/id6758150150)); SnapReminder limits scans in free tier. Evidence is listing-based, not review quotes.
9. **Extraction is a suggestion that needs verification; context lost.** Cropped screenshots omit location; dates need checking ([vendor blog](https://nemos-landing.pages.dev/blog/best-screenshot-organizer-apps-iphone), competitor-authored).
10. **Library and import friction; screenshots left duplicated.** Captureist reviewer could not import from other albums or delete originals after import ([App Store](https://apps.apple.com/us/app/captureist/id6443865506)). Related: backlog never revisited, "future me will handle this" ([Unbury on Product Hunt](https://www.producthunt.com/p/unbury/unbury), via search snippet).

Also notable: platform fragility (Circle to Search share removal and bugs, links above) and device gating (Apple Intelligence hardware only).

## 4. Implications for design (brief)

- Gap: breadth of action types beyond calendar/reminder, and cross-platform parity (Apple's flow is iPhone 15 Pro+, Pixel's is Pixel-only).
- Trust: on-device-by-default with explicit cloud opt-in addresses complaints 1-3.
- Automatic backlog processing without hard daily caps addresses 4 and the "never revisited" pattern.
- Always show an editable preview before commit (complaint 9).
- Free tier must include a working core action; reliability of notifications is table stakes (7).

## 5. Evidence limits
No Reddit or Play Store review text was retrievable with these tools; the 71% Reddit poll figure cited by one blog is unverified and was not used. Most third-party iOS apps have fewer than 5 ratings, so complaints 6, 7, 10 are anecdotal. Recommend a follow-up pass with direct Play Store and Reddit access.
