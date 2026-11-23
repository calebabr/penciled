# SPRINT_PLAN.md: Screenshot Actions beta

Status: plan only, written 2026-11-20. Nothing is built. Source of truth: `BUILD_HANDOFF.md` (component IDs, Accept lines, gates, cut list). Where this plan and the handoff disagree, the handoff wins. Every session count is an estimate.

---

## 1. Overview

**Goal:** testers install the beta from external TestFlight and Play internal by **Wed–Fri Jan 13–15, 2027**.

**Shape:** 33 sprints. 32 build sprints cover all 39 components (53 sessions, the same as the handoff's sizing), and SPR-33 is the release candidate (about ½ session). A sprint is 1 or 2 fresh ~5-hour Claude Code sessions. Each one ends committed, with tests green and the STATUS files updated, and can be tested on its own.

**Order:** foundation and store lead time come first. The Android worker gate falls on Dec 2. Next come the design system (CP1), then the server and AI chain, device data, the executor and the pipeline. Confirm screen → external TestFlight review build (RB1, ~Dec 21) → core loop (CP2, ~Dec 23). Holiday week: eval set and bug fixing. Then the rest of the screens in the fixed order Home → Read-only → Settings → Onboarding. Then a11y → polish → Maestro → RC.

**Session-capacity assumption:**

| Week | Dates | Baseline (sessions) | Fallback (sessions) |
|---|---|---|---|
| W1 | Fri Nov 20 – Wed Nov 25 | 7 (front-loaded) | 5 |
| W2 | Nov 26 – Dec 2 (Thanksgiving) | 5 | 4 |
| W3 | Dec 3 – 9 | 7 | 5 |
| W4 | Dec 10 – 16 | 7 | 5 |
| W5 | Dec 17 – 23 | 7 | 5 |
| W6 | Dec 24 – 30 (holiday) | 3 (1 kept for RB1 fixes and bugs) | 2 |
| W7 | Dec 31 – Jan 6 | 7 | 5 |
| W8 | Jan 7 – 13 (+ Jan 14) | 7 + 1 | 5 + 1 |
| **Total to RC** | | **≈50** | **≈37** |

(added: purchases extension; added: pricing pass) **Capacity note:** at most ~0.75 session is absorbed in total (~0.5 purchases + ~0.25 pricing) across SPR-02, 04, 08, 21 and 25, inside existing slack. No sprint is added, delayed, reordered or resized; the whole-number session counts above and in §2 do not change.

**What the numbers mean:**
- **Baseline (~6–7 a week; the plan assumes 7 in full weeks):** about 50 sessions are available, about 49 after the W6 reserve. Demand is 53.5 (53 + RC). The handoff's 20% buffer does not exist. **The cut list is the buffer.** The plan of record takes cuts 0, 3, 4, 9 and 10 at trigger T1 (Dec 3) and cuts 1 and 5–8 at T2 (CP2). Cut 11 is held as the first contingency. That lands RC on Jan 13–14 with roughly zero slack.
  - At a steady **6 a week**, even all 12 cuts leave the plan about 3–4 sessions short. That becomes a Chair decision (§5).
- **Fallback (~4–5 a week):** about 37 sessions. Every planner cut together saves about 5.85, plus about 1 more if the Android worker fails on Dec 2. That still leaves a gap of about 9–11 sessions.
  - No combination of planner cuts saves this date. At CP0 (Nov 25) the Chair must choose:
    - (a) move the beta to about Jan 27–29 and keep scope; or
    - (b) run an Android-only beta, which saves about 4 sessions, plus about 1 week of date slip.
  - The planner's recommendation is (a), because it keeps both magic moments and the never-cut polish.
- **Measuring capacity:** count completed sessions at CP0 against plan. W1 at 7 means baseline; W1 at 5 or fewer means fallback.

**Human-only track (builder, no Claude session):** day 1 — Apple and Play enrolment, provider account/DPA/$25 cap, SP-6 desk research; W1–W2 — collect, name-swap and hand-label SP-5's 50 own images (long pole of the eval chain) and get the reference devices (2022 mid Android, Samsung, older iPhone, low-end 2020 Android); by RB1 — host the privacy-policy URL; from CP2 — recruit ~50 testers.

---

## 2. Sprints (in order)

**Field key:**
- **Lane:** handoff §6 lane (A server, B eval, C design system, D Android native, E device data/pipeline, F actions, G native config, which has a single owner).
- **∥:** may run in parallel with the named sprint. Their files are disjoint, but they share the weekly cap. This only pays off while waiting on EAS cloud builds.
- **Exit:** the Accept lines from the handoff. "Done" means all of them pass, the commit is made, and STATUS is updated.

**Every sprint** reads root `STATUS.md`, its entry here, its BUILD_HANDOFF §2 entries and each touched component's `STATUS.md`; it leaves root and component `STATUS.md` + checklists updated, `docs/spikes/SP-n.md` for any spike, green tests and commits (no push unless asked). Fields below list only sprint-specific extras.

### SPR-01 · Monorepo and dependency matrix
- **Week:** W1 · **Sessions:** 1 · **Lane:** all/G · **Deps:** none · **∥:** —
- **Components:** COMP-REPO (incl. SP-13)
- **Goal:** scaffold `apps/mobile`, `server`, `shared`, `eval`, `tools`, CI. Pin the Expo SDK. Build a dev client on both phones.
- **Exit:** SP-13 recorded (one dev build per platform boots and calls expo-sqlite, RN ML Kit, FlashList v2, Reanimated, expo-share-intent, expo-calendar, expo-media-library, expo-secure-store and the fonts). CI green on an empty PR. Secret scan blocks a planted fake key. ESLint fails on a raw hex in `src/ui`. No-content-log grep job exists. Metro on Windows drives both phones.
- **Read first:** BUILD_HANDOFF §1.3–1.4, §1.7.
- **Leave:** root `STATUS.md` and `CLAUDE.md` (project hard rules, §4 template pointers), `docs/spikes/SP-13.md`, `.gitignore` with `.env*`.
- **Risk / fallback:** the ML Kit wrapper fails on iOS new arch → use the listed fallbacks and **escalate to the Chair on day 2** (no Swift allowed).

### SPR-02 · Contracts v1 (frozen)
- **Week:** W1 · **Sessions:** 1 · **Lane:** shared · **Deps:** 01 · **∥:** 03
- **Components:** COMP-CONTRACTS
- **Goal:** schemas: extract request/response, ProposedAction, errors, `rules.json` + fixture format, `thresholds_vN.json`, inbox JSON (`pending_app`), `worker_config`, `behavior_event` enums. Generate zod and pydantic types.
  - (added: purchases extension) Also the `nothing_subtype` (`receipt_order | shipping | booking | meme | other`), `guard_reason` counts + `receipt_like`, and `deadline_origin` (`printed_return_by | other`) enums, with matching `behavior_event` enum values.
  - (added: pricing pass) Also `tier` (token claim, default `free`), the optional `quota{tier,state}` response object, and the pricing enums (`pro_door_event`/`pro_feature`, `wtp_bucket`, `plan_pref`, `shadow_cap_hit`, `import_cap_hit`, `usage_day_bucket`, `search_zero_result`, `cap_tier`).
- **Exit:** pydantic ↔ zod round-trip on 20 fixtures, including `worker_config`. Unknown keys are dropped. `schema_version` is present in both directions. Tag `contracts-v1`.
  - (added: purchases extension) The 20 round-trip fixtures include one nothing-to-do per subtype and one deadline per origin. **Must land before the CP0 freeze Nov 25.**
  - (added: pricing pass) The 20 round-trip fixtures include one response with `quota` and one without; an unknown client-sent `tier` is dropped. Must land before the CP0 freeze Nov 25; tag stays `contracts-v1`.
- **Read first:** DESIGN §3.3 and §5 for the field lists (only if the handoff is unclear).
- **Leave:** `shared/CHANGELOG.md` with the rule "additive only, version bump required".
- **Risk / fallback:** churn breaks lanes → after CP0, `shared/` is read-only except in a dedicated bump session.

### SPR-03 · Store pipeline and share-extension spike
- **Week:** W1 · **Sessions:** 2 · **Lane:** G · **Deps:** 01 · **∥:** 02, 04, 05 (while waiting on EAS)
- **Components:** COMP-STORE (SP-1), COMP-SHARE-IOS slice A (SP-3 spike on hello-world)
- **Goal:**
  - Create the bundle IDs, the App Group, the App Store Connect record and the Play internal track.
  - Push hello-world through TestFlight internal and Play internal.
  - Add the `expo-share-intent` config plugin. Check that an image arrives, that the extension opens the app unaided, and the timing.
- **Exit:** both hello-world builds installed **from the stores** on real devices by **Wed Nov 25**. SP-3 spike result recorded: an image arrives, the extension opens the app 20/20 or not, rough Reading-to-open time. Desk check whether EAS Workflows or Maestro Cloud can run iOS flows (SP-16 pre-check).
- **Leave:** `docs/spikes/SP-1.md`, `SP-3.md`, and `docs/store/LEADTIME.md` (enrolment status, review dates to verify, tester list plan).
- **Risk / fallback:**
  - Identity verification is still pending → Android-only internal builds continue; escalate if it is not cleared by Dec 2.
  - The spike fails to open the app → "Saved. Open the app to review." copy and tell the Chair.
  - The plugin fails outright → fall back to `expo-sharing`.

### SPR-04 · Server core
- **Week:** W1 · **Sessions:** 2 · **Lane:** A · **Deps:** 02 · **∥:** 03
- **Components:** COMP-SERVER-CORE
- **Goal:** register, extract shell, `DELETE /v1/me`, statuses, quota, idempotency (status in Postgres, result in memory), content-free 422 handler, log scrubbing, deploy one warm instance, host secrets.
  - (added: pricing pass) Per-tier limits are read from config (`tier_limits`); `tier` comes from the token record only.
- **Exit:**
  - pytest for each status code.
  - (added: pricing pass) A config change to `tier_limits` changes the enforced limit (test).
  - In-flight duplicate → 202. A `done` duplicate is served from memory with no provider call. Text and image keys never collide.
  - Delete leaves zero rows for the token hash. Schema check finds **no content column**.
  - **422 canary**: the marker appears in neither the response nor the logs. Log capture shows no body text.
  - The server is deployed (hello).
- **Leave:** `server/STATUS.md` with deploy notes. **No secret values in any file.**
- **Risk / fallback:** a cold start breaks the SLO → min-instances = 1.

### SPR-05 · LLM proxy and latency spike
- **Week:** W1 · **Sessions:** 1 · **Lane:** A · **Deps:** 04 · **∥:** 03
- **Components:** COMP-LLMPROXY (SP-11)
- **Goal:** provider adapter, `prompts/v1` with `cache_control`, structured outputs, `effort: low`, escalation path, cost accounting.
- **Exit:** contract tests against a recorded-response fake. `cache_read_input_tokens > 0` from the 2nd live call. SP-11 report (p50 ≤1.5 s, p95 ≤4 s, mean ≤$0.002). Pick an arm.
- **Leave:** `docs/spikes/SP-11.md`.
- **Risk / fallback:** p95 >6 s in both arms → Chair re-opens the SLO before CP2.
- **CP0 closes here.**

### SPR-06 · Real-screenshot test
- **Week:** W2 · **Sessions:** 1 · **Lane:** B · **Deps:** 01, 05 · **∥:** —
- **Components:** COMP-EVALSET slice A (SP-5): label schema, manifest validator, the 50 own images run through the dev build's ML Kit → script → Haiku.
- **Exit:** SP-5 recorded: text-only failure %, whether the image arm fixes failures, chat-anchor accuracy, text p50. Manifest validator passes on the own half. Own images are **outside git** (hashes only).
  - (added: purchases extension) The own half includes receipt/order fixtures (inside the ~150 images, not additional): with/without printed "Return by", a policy sentence without a date, order number + card last-4, one guard-blocked. Own or synthetic only.
- **Leave:** `docs/spikes/SP-5.md` with the chosen image policy and the chat-heuristic findings that SPR-08 needs.
- **Risk / fallback:** results trigger the SP-5 fallbacks (image-on-escalation final; chat dates `needs_review`).

### SPR-07 · Android notifications and app-closed worker spike (Dec 2 gate)
- **Week:** W2 · **Sessions:** 2 · **Lane:** D/F · **Deps:** 02, 04 · **∥:** —
- **Components:** COMP-NOTIFY; COMP-ANDROID-WORKER slice A (SP-2: content-URI trigger re-enqueued each run, watermark, folder filter, seen-file dedupe, ML Kit OCR, stub rules, POST to the real server, notification)
- **Exit:**
  - NOTIFY: unit table of gate_state → push or no push. Channels exist. [Review] is the only action.
  - **SP-2: ≥19/20 notifications on Pixel and Samsung with the app swiped away; p95 ≤10 s; correct folder filter; drain <1%/h.**
- **Leave:** `docs/spikes/SP-2.md` with the gate verdict, plus `modules/android-worker/STATUS.md`.
- **Risk / fallback:** vendor battery killers. **Gate Wed Dec 2:** a fail ships ST-AUTODETECT-FALLBACK (Android uses the iOS model); SPR-09 is then replaced by about ½ session of fallback wiring.

### SPR-08 · Guard, chat heuristic, gate and redaction rules (TS, then Kotlin)
- **Week:** W2 · **Sessions:** 2 · **Lane:** E/D · **Deps:** 02, 06 · **∥:** —
- **Components:** COMP-RULES (SP-12)
- **Goal:** `rules.json`, the TS `classify()`, then the Kotlin port. **Do TS first, Kotlin last**, so a Dec 2 worker failure can skip the Kotlin half.
  - (added: purchases extension) Add the `receipt_like` keyword list and the `deadline_origin` evidence pattern to `rules.json`, with Kotlin and TS parity fixtures. Guard thresholds and patterns unchanged (~0.1 session, absorbed).
- **Exit:** EVAL-GUARD-PARITY identical on the shared fixtures (≥20 chat, ≥20 not-chat). Chat recall ≥0.95. Sensitive recall ≥0.97 on 25 synthetic. AI-GATE recall ≥0.98. Outbound payload scan finds no email, phone or 7+ digit run.
- **Leave:** `docs/spikes/SP-12.md`.
- **Risk / fallback:** recall is short → widen patterns, biased toward false positives. **Release-blocking.**

### SPR-09 · Android worker integration
- **Week:** W3 · **Sessions:** 1 · **Lane:** D · **Deps:** 07, 08 · **∥:** 10
- **Components:** COMP-ANDROID-WORKER slice B (Kotlin rules wired in, `worker_config` read and app-side synchronous write, inbox JSON, backup exclusion, wipe hooks)
- **Exit:**
  - Instrumented or Gradle tests: sensitive fixture → no network. **Chat toggle on → zero requests. `worker_config` missing or stale → zero requests, `pending_app` inbox.**
  - Toggle honoured by a screenshot 1 s later. No image unless the opt-in is on and the item is not-chat.
- **Risk / fallback:** a third session is needed → split per handoff §2 and take it from buffer. Never relabel the component L.

### SPR-10 · Theme and fonts
- **Week:** W3 · **Sessions:** 1 (½ if cut 10 is taken) · **Lane:** C · **Deps:** 01 · **∥:** 09, 13
- **Components:** COMP-UI-THEME (SP-15)
- **Exit:** Jest contrast test (≥4.5 text, ≥3 non-text), light and dark. Increase Contrast set only if cut 0 is *not* taken and RN exposes the setting. ESLint token rule active. Tabular digits at 200% on both phones (scripted manual).
- **Read first:** UI.md §2.1–2.3, §7.5.
- **Leave:** `docs/spikes/SP-15.md`.
- **Risk / fallback:** no Casual statics → instance them with fonttools and commit the TTFs. Otherwise use the system font (cut 10).

### SPR-11 · Core component library and `/states`
- **Week:** W3 · **Sessions:** 2 · **Lane:** C · **Deps:** 10, 02 · **∥:** 13
- **Components:** COMP-UI-LIB (SP-14)
- **Exit:** every UI.md §7.3 core variant (ACTIONCARD, FIELDROW, BTN, THUMB, SHEET, TOAST, BADGE, SKELETON) renders in `/states`, light/dark/200%, on both phones. Lint finds no raw style values. formSheet decision recorded.
- **Read first:** UI.md §3, §7.3, §7.6.
- **Leave:** `docs/spikes/SP-14.md`.
- **Risk / fallback:** formSheet on Android → `@gorhom/bottom-sheet` on Android only.

### SPR-12 · Plain components and motion
- **Week:** W3 · **Sessions:** 2 · **Lane:** C · **Deps:** 11 · **∥:** 13
- **Components:** COMP-UI-LIB-PLAIN; COMP-UI-MOTION (+ SP-10 fling on a throwaway 10k in-memory list of pre-generated thumbnails; the real seeder comes in SPR-32)
- **Exit:**
  - All plain components appear in `/states`. The grid passes SP-10 (≥55 fps, <1% dropped, <400 MB).
  - Ink-in ≤700 ms measured. Write starts before the first frame (instrumented log). Reduced motion → 150 ms cross-fade (if cut 9: cross-fade only).
  - **CP1 sign-off:** the builder walks `/states` on both phones against the §7.6 checklist.
- **Risk / fallback:** FlashList v2 fails → v1, or FlatList + `getItemLayout`. Jank → UI-thread worklets only.

### SPR-13 · Date resolver
- **Week:** W3–W4 · **Sessions:** 2 · **Lane:** A · **Deps:** 02 · **∥:** 10–12
- **Components:** COMP-RESOLVER-DATE
- **Exit:** **EVAL-DATE ~60 cases 100% under 3 process timezones.** Property test over 10k random cases: always an IANA tz, never a past alarm. Past start → `past` + blocking.
- **Leave:** re-run SP-5 dates through the resolver and append the result to SP-5.md.
- **Risk / fallback:** DST and ambiguous-tz cases must flag, never guess.

### SPR-14 · Ground, validate, propose, and gate code
- **Week:** W4 · **Sessions:** 2 · **Lane:** A · **Deps:** 05, 13 · **∥:** 15
- **Components:** COMP-RESOLVER-GVP; COMP-GATE (code on the DESIGN §5.5 initial constants; the threshold freeze waits for SPR-26)
- **Exit:** EVAL-GROUND-01 zero violations. 10 injection fixtures give no ungrounded action. resolve_only makes no provider call. GATE cap unit table passes. **EVAL-GATE-01: 0 Ready with an ungrounded required field** on fixtures. Hard overrides come first.
- **Risk / fallback:** the fuzzy threshold is wrong on OCR noise → tune on dev fixtures only.

### SPR-15 · Core DB and ingest
- **Week:** W4 · **Sessions:** 2 · **Lane:** E (+G for `dataExtractionRules` plugin) · **Deps:** 02 · **∥:** 14
- **Components:** COMP-COREDB; COMP-INGEST
- **Exit:**
  - Migration empty → v1. `writeBatch` of 1,000 rows <1 s on a mid Android. `logEvent()` is live, so the behaviour log writes from the first card. CI grep finds no free-text column in `behavior_event`.
  - 200 repeat imports → 1 row. Import 25 → 20 + ST-IMPORT-CAP. Processing started ≤2 s p95.
- **Leave:** native change batched into **native batch NB2** (one iOS cloud build with SPR-16).
- **Risk / fallback:** thumbnail cost on low-end phones → smaller thumbnails.

### SPR-16 · OCR and privacy plumbing
- **Week:** W4 · **Sessions:** 2 · **Lane:** E/G · **Deps:** 01, 04, 15 · **∥:** 17
- **Components:** COMP-OCR; COMP-PRIVACY (SP-6 final)
- **Goal:**
  - OCR: downscale, ≤2 decodes.
  - Privacy: token in secure-store; delete-one and delete-all including `inbox/`, `seen`, `worker_config` and `DELETE /v1/me`; final ONB-2 and Privacy copy; privacy policy text; Privacy Manifest; a minimal AI-data consent route (`app/onboard/consent.tsx` using CMP-DATAFLOW) for RB1, later absorbed by SPR-28.
- **Exit:** OCR line count ±10% on 20 fixtures, p95 ≤1.2 s. Delete-all integration test (server zero rows, local files empty). No "not stored" claim unless SP-6 verified it. Policy URL live.
- **Risk / fallback:** retention terms unclear → state the longest published period.

### SPR-17 · Executor
- **Week:** W4–W5 · **Sessions:** 2 (top of M) · **Lane:** F · **Deps:** 15, 02 · **∥:** 16, 18
- **Components:** COMP-EXECUTOR (SP-7, SP-8)
- **Exit:**
  - **EVAL-SAFE-04 fuzz: 0 writes without a confirm event.** Written == displayed (100 random). Double tap → one item.
  - Reconcile adopts on a marker. **Relaunch with `executing` and no marker → no write, Draft + ST-RECONCILE.**
  - Denial keeps the Draft. Fallback path logs "Sent to Calendar". Dismiss is side-effect free. Write started ≤500 ms.
  - SP-7/SP-8 device runs recorded, plus EVAL-BAR-08 alarms p95 <2 min on battery saver (20 per platform).
- **Risk / fallback:** a third session is needed → split (write/reconcile vs fallbacks + permissions). All-day drift → timed 09:00 deadlines.

### SPR-18 · Pipeline and API client
- **Week:** W5 · **Sessions:** 2 · **Lane:** E · **Deps:** 08, 14, 15, 16 · **∥:** 17
- **Components:** COMP-PIPELINE
- **Exit:**
  - Kill-app-mid-job resumes.
  - The fake server proves **≤3 automatic calls per item** with escalation included, a stable key across retries, and different keys for text vs image. Offline and 503 don't use up attempts.
  - ST-OFFLINE then auto-resume. 413 → ST-BASIC. 426 → ST-UPGRADE. Placeholders restored on the card.
- **Risk / fallback:** JS jank → serial processing and yield between items.

### SPR-19 · Confirm sheet, then external review build RB1
- **Week:** W5 · **Sessions:** 2 · **Lane:** screens · **Deps:** 12 (CP1), 14, 17, 18 · **∥:** —
- **Components:** COMP-UI-CONFIRM
- **Goal:** build the Confirm sheet. Then send RB1 (import → Draft → Confirm → Add) to **external TestFlight Beta App Review ~Mon Dec 21**, with the consent route and policy URL.
- **Exit:** matches UI.md §4.3. **MAE-MAGIC passes (Android, local).** Every gating, field and action state is in `/states`. Tap → write started ≤500 ms. Focus lands on the first blocking flag (scripted screen-reader check). Add exists **only** here. The button is never disabled ("Check date to continue"). RB1 submitted.
- **Read first:** UI.md §4.3, §5 (states), §6 (motion).
- **Risk / fallback:** picker accessibility; formSheet keyboard. If Confirm slips past Dec 22, still submit RB1 from the best working build before Apple's holiday cutoff (verify dates).

### SPR-20 · Undo and share extension (CP2)
- **Week:** W5–W6 · **Sessions:** 2 · **Lane:** F ∥ G · **Deps:** 17, 03, 15 · **∥:** internally (UNDO and SHARE files are disjoint)
- **Components:** COMP-UNDO; COMP-SHARE-IOS slice B (ingest wiring, Reading card ≤1 s)
- **Exit:**
  - Undo removes the item on both platforms. Edited in Calendar → dialog. Already gone → "already removed". Write-only → "can't undo from here".
  - **20 shares on TestFlight:** opens unaided 20/20 (or the fallback copy), Reading ≤1 s, started ≤2 s p95, no crash.
  - **CP2:** frames A0–A7 (or the Android fallback) and I0–I7 demonstrated. Executor gates pass. GATE gives real `gate_state`. Behaviour rows are written.
- **Risk / fallback:** EAS turnaround → batch as NB3. Fallback chain: `expo-sharing`, then import + catch-up only (Chair told).

### SPR-21 · Eval set completion
- **Week:** W6 · **Sessions:** 1 · **Lane:** B · **Deps:** 06 · **∥:** any
- **Components:** COMP-EVALSET slice B (Playwright generator: 100 synthetic images; merge the hand labels; dev/holdout split; hash-lock)
- **Exit:** manifest validator passes. Class counts match (≈30 event incl. 10 RSVP, 20 deadline, 25 sensitive, 25 noise, 50 own). Holdout hash-locked (EVAL-META-02). Chat labels present.
  - (added: purchases extension) 10 to 15 receipt/order fixtures sit inside the ~150 images (not additional), including ≥2 injection-in-receipt cases (counted toward the 10 injection fixtures). Labels carry `nothing_subtype` and `deadline_origin`. Manifest counts updated; Exit otherwise unchanged.
- **Risk / fallback:** hand-labelling is behind → this sprint waits. The labelling is human work and must be finished in W1–W5.

### SPR-22 · Search and iOS catch-up
- **Week:** W7 · **Sessions:** 2 (1 if cut 11) · **Lane:** E · **Deps:** 15 · **∥:** 24
- **Components:** COMP-SEARCH (SP-9); COMP-CATCHUP (SP-4)
- **Exit:** search p95 ≤300 ms at 10k on a mid Android. Recall@5 report. Rebuild after index.db is deleted. SP-4: 10 screenshots + 10 photos → only the screenshots. Limited Photos → ST-PERM-PHOTOS-LIMITED (scripted manual).
- **Risk / fallback:** no trigram → unicode61 + prefix. No subtype → dimension filter.

### SPR-23 · Home screen
- **Week:** W7 · **Sessions:** 2 · **Lane:** screens · **Deps:** 12, 18, 20, 22 · **∥:** 24
- **Components:** COMP-UI-HOME
- **Exit:** matches UI.md §4.2. Cards carry **[Review] only**. Every Home ST-* is reachable in `/states` or Maestro. Added list with swipe-Undo. QA-PERF-01/02/05 at 10k (interim).
- **Risk / fallback:** banner priority and search/chip interplay → unit-test the priority table.

### SPR-24 · Eval harness
- **Week:** W7 · **Sessions:** 2 · **Lane:** B · **Deps:** 21, 14, 08 · **∥:** 22, 23
- **Components:** COMP-EVALHARNESS
- **Exit:** tier-1 CI run <10 min (≈$1, cached). Mock server asserts **zero requests for the sensitive set** (EVAL-SAFE-01/02/03). Report has the EVAL-CLS/FLD/PERF/COST sections and the calibration hook.
- **Risk / fallback:** OCR fidelity mismatch → note it in the report and use device-extracted text for the own half.

### SPR-25 · Beta counts and behaviour log
- **Week:** W7–W8 · **Sessions:** 2 (1½ if cut 6) · **Lane:** E (+A server metrics endpoint) · **Deps:** 15, 04 · **∥:** 24
- **Components:** COMP-METRICS; COMP-BEHAVLOG
- **Exit:** **EVAL-BAR-14 payload scan finds 0 content.** Counters reconcile with a scripted 10-card session. Shadow clock test passes and **no notification is ever scheduled**. No free-text column.
  - (added: purchases extension) Enum dims on `metric_daily` for the new fields; the F8 report computes the promotion trigger (receipts ≥15% of processed screenshots AND ≥30% of those with a printed return date); the scripted 10-card session includes one receipt; the EVAL-BAR-14 scan covers the new dims.
  - (added: pricing pass) Pricing enum dims added (see SPR-02 list); EVAL-BAR-14 still finds 0 content.
- **Risk / fallback:** free text in a dimension → server-side enum validation.

### SPR-26 · Calibration and threshold freeze
- **Week:** W8 · **Sessions:** 1 (½ if cut 7) · **Lane:** B · **Deps:** 24 · **∥:** 27
- **Components:** COMP-CALIB; COMP-GATE threshold-freeze acceptance
- **Exit:** report renders (ECE, Brier, reliability, state mix, Ready precision, CIs). `thresholds_v1.json` is reproducible from a fixed seed. GATE loads it. EVAL-GATE-01 on the holdout. **Human-approved baseline-bump commit with the report attached.**
- **Risk / fallback:** the report is coarse (about 30 errors) → accepted.

### SPR-27 · Read-only view and Settings
- **Week:** W8 · **Sessions:** 2 (1¾ if cut 5) · **Lane:** screens · **Deps:** 23, 20, 16, 25 · **∥:** 26, 32
- **Components:** COMP-UI-READONLY → COMP-UI-SETTINGS (in that order)
- **Exit:** matches UI.md §4.3 read-only and §4.4. Delete-one removes the row, OCR and thumbnail. No sensitive toggle and no "Send anyway" (test). ST-HISTORY-EMPTY renders. MAE-UNDO History path passes.
  - (added: pricing pass) Note: the optional Settings "Pro preview" row (cut-list item P0, UI.md §4.4) is about ¼ session of UI work inside this sprint. It is the first cut and is not needed for the schedule.

### SPR-28 · Onboarding
- **Week:** W8 · **Sessions:** 2 (1½ if cut 8) · **Lane:** screens · **Deps:** 27, 19, 16, 20 · **∥:** 32
- **Components:** COMP-UI-ONBOARD
- **Exit:** matches UI.md §4.1. **No permission prompt before ONB-2** (Maestro assertion). MAE-PERM-DENIED passes. ONB-3 writes nothing (calendar mock). iOS coaching uses real TestFlight screenshots. Invite-code registration works.

### SPR-29 · Accessibility pass
- **Week:** W8 · **Sessions:** 1 · **Lane:** screens · **Deps:** 28 · **∥:** 32
- **Components:** COMP-UI-A11Y
- **Exit:** scripted VoiceOver and TalkBack walkthroughs of the 3 Maestro paths with no sighted help. 200% screenshots show no clipping. Contrast test green.

### SPR-30 · Polish pass (never cut)
- **Week:** W8 · **Sessions:** 2 · **Lane:** screens · **Deps:** 29 · **∥:** —
- **Components:** COMP-UI-POLISH
- **Exit:** the §2.10 coverage table is 100% ticked, with a screenshot per state in light/dark/200% on both phones. Zero open core-tier issues. QA-PERF re-run. **CP4a.**

### SPR-31 · Maestro final run
- **Week:** W8 · **Sessions:** 1 · **Lane:** QA · **Deps:** 30 · **∥:** —
- **Components:** COMP-QA-MAESTRO (SP-16)
- **Exit:** MAE-MAGIC, MAE-PERM-DENIED and MAE-UNDO pass on Android, and on iOS through the cloud runner or a scripted manual run on the iPhone.

### SPR-32 · Performance
- **Week:** W7–W8 · **Sessions:** 1 (¾ if cut 1) · **Lane:** `tools/perf` · **Deps:** 22, 12; final run after 23 · **∥:** 26–29
- **Components:** COMP-PERF
- **Exit:** 10k/30k seeder. Release-build QA-PERF-01..07 (median of 10) within budget on a 2022 mid Android and an older iPhone. Cost projection for 50 and 300 testers. $25 cap and kill switch tested. **CP4b.**

### SPR-33 · Release candidate
- **Week:** Jan 12–14 · **Sessions:** ~½ · **Deps:** all
- **Exit:** every §7.3 pre-beta gate green. RC uses the same version as approved RB1, uploaded to TestFlight external, and rolled to Play internal. Invite codes issued. Tester guide written. **CP5.**

---

## 3. Calendar (baseline, after the T1/T2 default cuts)

| Week | Sprints (session #) | Checkpoints, gates and lead-time tasks |
|---|---|---|
| **W1** Nov 20–25 | 01 (1), 02 (2), 03 (3–4), 04 (5–6), 05 (7) | Day 1: Apple and Play enrolment, provider account, SP-6 desk. Days 1–2: EAS + bundle IDs + **App Group**. **Hello-world in both stores by Wed Nov 25.** **CP0 Wed Nov 25** (repo, CI, contracts v1 frozen, server hello, SP-1/6/11/13 done; capacity measured → baseline or fallback declared) |
| **W2** Nov 26–Dec 2 | 06 (8), 07 (9–10), 08 (11–12) | Thanksgiving. SP-5 labels by hand. **Android worker gate Wed Dec 2** (SP-2 verdict; fail → ST-AUTODETECT-FALLBACK, SPR-09 replaced) |
| **W3** Dec 3–9 | 09, 10, 11, 12, 13 (start) | **T1 cut decision Thu Dec 3.** **CP1 ~Tue Dec 8** (`/states` sign-off) |
| **W4** Dec 10–16 | 13, 14, 15, 16, 17 (start) | Native batch NB2 (one iOS cloud build). Privacy-policy URL live. Recruit testers from here |
| **W5** Dec 17–23 | 17, 18, 19, 20 | **RB1 to external TestFlight Beta App Review ~Mon Dec 21** (verify Apple holiday dates; latest Tue Dec 22). **CP2 ~Wed Dec 23**: 2–3 internal testers on Play internal and TestFlight internal. **T2 cut decision** |
| **W6** Dec 24–30 | 21, + 1 session reserved | Holiday: eval set, RB1 rejection fixes, bugs only. No new features |
| **W7** Dec 31–Jan 6 | 22, 23, 24, 25 (start), 32 (seeder) | **T3 Sun Jan 3** (cut 11?). CP3b feature-complete check slips to W8 (see note) |
| **W8** Jan 7–13 | 25, 26, 27, 28, 29, 30, 31, 32 (final) | **T4 Thu Jan 7** (cut 12, Chair). Thresholds frozen ~Jan 7. **CP3b feature complete ~Jan 9.** **CP4a ~Jan 12. CP4b ~Jan 12** |
| Jan 12–14 | 33 | **CP5 RC ~Jan 13.** Testers install **Jan 13–15** |

**Note on CP3:** at this capacity the handoff's CP3 splits into **CP3a Dec 21** (RB1 submitted; the lead-time item holds) and **CP3b ~Jan 9** (feature complete). This is safe only if later builds of the approved version skip full review; **verify in SPR-03**, and if not, pull SPR-20 slice B (share extension) before RB1.

**Native batch windows** (each is one iOS EAS cloud build; Lane G owns `app.config.ts`, `eas.json`, `plugins/`):
- NB1: SPR-01/03
- NB2: SPR-15/16
- NB3: SPR-20/22
- NB4: RC

JS-only sprints never trigger a cloud build. Budget one paid EAS month if the free quota runs out (verify).

**Fallback calendar (4–5 a week):** same order, about 1.5× later: CP1 ~Dec 14, RB1 when SPR-19 closes (~Jan 5), CP2 ~Jan 8, beta ~**Jan 27–29** under option (a). The Nov 25 hello-world and Dec 2 gate dates do not move.

---

## 4. Per-session prompt template

Paste this at the start of every fresh Claude Code session. Fill in the `<…>` fields from the root `STATUS.md` "Next" line.

```
You are continuing the Screenshot Actions beta build. Session <N> of sprint <SPR-xx: title>
(session <k> of <size>). Today is <date>. Work only on this sprint's components.

READ FIRST (in order, nothing else unless a detail is missing):
1. STATUS.md (root): sprint board, last commit, blockers, cuts taken.
2. SPRINT_PLAN.md entry for <SPR-xx>, plus §5 cut list status.
3. BUILD_HANDOFF.md §1.7 (hard rules) and §2 entries for <COMP-IDs>.
4. <component folder>/STATUS.md and acceptance checklist for each component touched.
5. <only if UI> UI.md §<sections>; <only if spike> docs/spikes/SP-<n>.md.
Run `git status`, `git log -5 --format='%an %ae %s'`, and the existing test suites
to confirm a green starting point. If they are red, fix or record that before new work.

DO:
- Implement the sprint's Exit criteria in the order listed; write tests first where
  the Exit line names an automated test.
- Stay in this sprint's lane/files. Do not edit shared/ (contracts) without a
  version-bump note; do not touch app.config.ts / eas.json / plugins/ unless this is
  the Lane G owner sprint; batch native changes into the named NB window.
- Record any spike in docs/spikes/SP-<n>.md (pass/fail, numbers, fallback taken).
- Stop at ~4.5 h of work or when Exit passes, whichever is first.

HARD RULES (never break):
- The model never executes an action; code validates; a calendar write happens only
  from a user tap on Add in the Confirm sheet. Cards and notifications carry [Review] only.
- Never log screenshot content (OCR text, images, fields, model output, request bodies)
  anywhere: logs, errors, crash reports, analytics, tests' snapshots of logs.
- Sensitive / chat-with-toggle / missing worker_config = zero network requests.
- Never read, print or commit .env files, API keys or secrets.
- UI uses src/theme.ts tokens only (no raw hex, no inline numeric styles).
- Date maths only in the server resolver. Thresholds/prompts change only via a
  human-approved baseline-bump commit.
- Commit only as the configured git identity (check `git config user.name/email`);
  NO Co-Authored-By, "Generated with", or any AI attribution line. Do not push unless
  the builder asks in this session.

LEAVE (before ending, even if unfinished):
- Tests green (or the failing test named in STATUS with the reason).
- <component>/STATUS.md: done / not done / next step / gotchas; checklist ticked.
- Root STATUS.md: update the sprint board, sessions used vs plan (+/-), blockers,
  any cut-trigger flag (see SPRINT_PLAN §5), and the exact "Next:" line for the
  next session.
- One commit per coherent step, message "<SPR-xx> <component>: <what>".
- Reply with: Exit criteria passed/failed, sessions used, next step.
```

Root `STATUS.md` always holds: current sprint and session k/size, last green commit, sessions used vs plan, cuts taken (with Chair notes for 6, 11, 12), gate results (Dec 2, SP-3), RB1/store status, and the next action.

---

## 5. Cut triggers

**Rules:**
- **Variance:** at each trigger, compute *sessions behind plan* = cumulative sessions used − the plan's cumulative count for the sprints completed.
- **Order and windows:** cut in handoff order. A cut whose **window** has closed (its component is already built) is skipped and gives no saving, and the next one is taken.
- **Reversing cuts:** if you are ahead of plan, reverse untaken cuts in reverse order, but only while their window is still open.
- **Never cut:** theme.ts, the component library and `/states`, the Draft/Added distinction, blocking flags and "Check … to continue", Undo everywhere, honest error/empty/offline/permission/sensitive states, ONB-2, dark mode, 200% text, the eval hard gates, the sensitive no-network rule, and UI-POLISH.

| Trigger | When | Cuts eligible (window) | Baseline default | Take if behind… |
|---|---|---|---|---|
| **T0** | CP0, Nov 25 | — | Declare baseline or fallback from W1 throughput (≥6 → baseline; ≤5 → fallback + Chair escalation, §1) | — |
| **T1** | Thu Dec 3, before SPR-10 | (added: pricing pass) **P0** Pro preview row (SPR-27; cut first); (added: purchases extension) **P1** receipt fixtures (SPR-06/21), **P2** purchase logging fields (SPR-02/25); P0, P1, P2 sit above item 0 and original items 0–12 keep their numbers; the contract and metric fields (P2 and the pricing fields) are decidable only until Nov 25; **0** Increase Contrast (SPR-10); **3** long-press source quote (SPR-11); **4** calendar colour dot (SPR-19); **9** ink-in flood (SPR-12); **10** Recursive fonts (SPR-10) | Take 0, 3, 4 (≈0.6). Take 9, 10 (≈1.0) unless ≥13 sessions were done by Dec 2 | Any deficit → all five |
| **T2** | CP2, ~Dec 23 | **1** 30k report (SPR-32); **5** Settings default-calendar and alerts rows (SPR-27); **6** shadow evaluator (SPR-25, Chair note); **7** calibration detail (SPR-26); **8** ONB-3 interactive sample (SPR-28) | Take 1, 5, 6, 7, 8 (≈2.0); the baseline is break-even without them | Always at baseline; reverse only if ≥2 sessions ahead |
| **T3** | Sun Jan 3, before SPR-22 | **11** iOS catch-up (SPR-22, Chair note; amends F1(b) and EVAL-BAR-12) | Hold | ≥1 session behind → take (saves 1) |
| **T4** | Thu Jan 7 | **12** Search/FTS5 (Chair decision; already built in SPR-22, so only the remaining perf/recall work is saved, ≈¼–½). If you foresee it at T3, cut 12 **before** SPR-22 to save the full 1–1.25 | Hold | RC cannot land by Jan 14 |
| **Beyond the list** | any | Chair decisions only: Android-only beta (SP-1/SP-3 iOS failure), date move | — | Deficit remains after T3 |

**Fallback (4–5 a week):**
- T0: declare fallback and escalate the date to the Chair.
- T1: take 0, 3, 4, 9, 10.
- T2: take 1 and 5–8, **plus 11 and 12** (Chair notes; cut 12 before SPR-22).
- Total saved ≈5.85, still about 9–11 short, so the date moves (§1).

**Hard-gate triggers (not cuts; they block the RC):** EVAL-DATE <100%, any network call on sensitive/chat-with-toggle/stale-config items, any ungrounded Ready card, fuzz <100%, a guard-parity break, or content in telemetry. Any of these stops feature work until fixed.

---

## 6. Risk register

| # | Risk | Likelihood / impact | Early signal | Mitigation / fallback |
|---|---|---|---|---|
| R1 | **Weekly cap gives fewer than 7 sessions** | High / High | W1 count at CP0 | Cut triggers §5; Chair date decision at T0; no parallel agents beyond EAS waits |
| R2 | Apple or Play identity verification delayed | Med / High | Not cleared by Nov 25 | Started day 1; Android-only internal builds meanwhile; escalate Dec 2 |
| R3 | **Beta App Review over the holidays** (RB1 rejected or slow) | Med / High | Apple holiday notice; rejection mail | Submit RB1 ~Dec 21; AI-consent tap + policy URL in RB1; 1 W6 session reserved; 3–5 days of January slack; RC keeps the same version |
| R4 | Later builds need full re-review (share-extension entitlement change) | Med / Med | Apple docs and the RB1 response | Verify in SPR-03; if needed, include the share ext in RB1 |
| R5 | **Android worker fails Dec 2 (SP-2)** | Med / Med | SPR-07 trial counts | Pre-decided ST-AUTODETECT-FALLBACK; Kotlin rules done last in SPR-08 to limit waste |
| R6 | **iOS share extension can't open the app or the plugin breaks (SP-3)** | Med / High | SPR-03 spike | "Saved. Open the app" copy; `expo-sharing`; import + catch-up; Chair told |
| R7 | RN ML Kit wrapper fails on iOS new arch (no Swift) | Low–Med / Critical | SP-13 day 2 | Chair escalation on day 2; Android-only scenario |
| R8 | EAS iOS quota or queue times | Med / Med | Queue >1 h | Native batch windows NB1–4; one paid month |
| R9 | **Hand-labelling of 50 own images is late** | Med / High (blocks threshold freeze = RC gate) | Labels <50% by Dec 9 | Human track W1–W5; synthetic labels are generator-made; cut 7 shrinks CALIB |
| R10 | Haiku latency or cost above SLO (SP-11) | Low–Med / Med | SPR-05 report | Pick the faster arm; Chair re-opens the SLO if p95 >6 s |
| R11 | Executor or worker needs a 3rd session | Med / Med | Session 2 Exit not met | Split per handoff; draw from cuts, never from polish |
| R12 | Contract churn after CP0 | Med / Med | PRs touching `shared/` | Additive only, version bump in one session |
| R13 | Polish squeezed at the end | High / High | SPR-29 start after Jan 10 | Polish is never cut; T3/T4 cuts fire first; RC on Jan 14 is the last day |
| R14 | Fresh session loses context or redoes work | Med / Med | Sessions-used variance | §4 template; STATUS discipline; commit per step |
| R15 | Reference devices unavailable (Samsung, 2022 mid, older iPhone) | Med / Med | Not in hand by Dec 2 | Borrow or buy in W1–W2; SP-2/SP-8/QA-PERF depend on them |
| R16 | Maestro on iOS without a Mac (SP-16) | Med / Low | SPR-03 desk check | Scripted manual run on iPhone (+½ session) |
| R17 | Tester recruitment over the holidays; >100 Android testers | Med / Med | <30 sign-ups by Jan 3 | Recruit from CP2; closed track if >100 Android |
| R18 | Content leaks into logs or telemetry, or a secret is committed | Low / Critical | CI grep, 422 canary, secret scan | Built into SPR-01/04/25 Exit; `.env*` ignored; blocks the RC |
| R19 | (added: purchases extension) Receipt logging data shows receipts <15% or printed dates <30% (promotion trigger not met) | Low / Low | SPR-25 F8 report | Ship expense CSV without return reminders; no Purchase type |

---

## 7. CP0 checklist (Nov 25)

- Working app name chosen before SPR-01 sets bundle IDs (app name, bundle IDs, App Group ID)
- (added: purchases extension) purchase logging enums are in `contracts-v1`
- (added: pricing pass) `tier`, `quota` and pricing metric enums are in `contracts-v1`

## 8. Post-beta list

- (added: pricing pass) PRICE-TIERS: unsized, dotted (not scheduled)
- (added: pricing pass) PRICE-IAP: unsized, dotted (not scheduled)

---
## User decision (2026-11-20): beta date stays Jan 13–15, 2027
The recommendation to move to Jan 27–29 was declined. Plan accordingly: apply cut triggers T0–T4 on schedule, re-measure sessions per week at CP0 (Nov 25), and escalate scope (e.g. Android-only beta) rather than the date if capacity falls below ~6 sessions/week. Logged as D23 in raw/chair_decisions.md.
