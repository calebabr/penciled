# 6. Review: cross-document contradictions and gaps

Scope: FEATURES, UI, DESIGN, BUILD_HANDOFF vs D1–D19. P0 = privacy/core-rule breach; P1 = wrong behaviour or false claim; P2 = builder will hit it; P3 = hygiene.
Counts: **P0 1 · P1 6 · P2 19 · P3 9**.

| # | Sev | A vs B | Conflict | Fix |
|---|---|---|---|---|
| 1 | P0 | DESIGN §3.8, BUILD WORKER "never opens SQLite" vs DESIGN §3.3 `kv` (token, watermark, settings) | The worker can't read the token, watermark, chat local-only toggle or image opt-in, so it would POST chat text against the user's setting. | Add a `worker_config` contract (EncryptedSharedPreferences) that the app rewrites on each settings change. Worker sends nothing if it's missing. Test: toggle on → 0 requests. |
| 2 | P1 | DESIGN §7.1 "server memory only, ≤10 min" + ONB-2 vs §3.4 `idempotency.result_json` in Postgres | Fields are on disk and in DB backups past 10 min. The copy is false. | Keep results in process memory, **or** change the copy and record backup retention in SP-6. |
| 3 | P1 | UI principle 2, frames A3/I4 (missing AM/PM blocks) vs DESIGN §5.4/C7 (`assumed`, cap 0.92 ⇒ Ready) | The demo flag and MAE-MAGIC rely on a blocking row the resolver never produces. | Keep C7. Use a real blocking case (weekday/date conflict, "12am") in the UI frames and the fixture. |
| 4 | P1 | BUILD rule 2 "card button for a Ready card", UI card [Add …] vs FEATURES core principle, SEC-INJ-CONFIRM "sheet that shows every field", D19 rationale | The card shows ≤2 field lines. End, calendar, alerts and sub-actions are hidden, yet a tap writes. | Ready card button = [Review] in beta. Update ACTIONCARD, A11Y-02, §5 tap counts and rule 2. |
| 5 | P1 | DESIGN C8/§7.1 "never chat image", SEC-CHAT, `is_chat` vs COMP-RULES `classify()` | No chat detector exists (source-app detection was removed). | Add a chat heuristic to rules.json (bias true) plus parity fixtures and a RULES Accept line. |
| 6 | P1 | DESIGN §3.7 key `HMAC:prompt:schema:rerun` vs AI-ESCALATE second call | The image call hits the 10-min cache and gets the text result back. | Add an `:img` key segment and count escalation within ≤3 calls. |
| 7 | P1 | DESIGN 422 vs SEC-LOG-NOCONTENT, BUILD rule 3 | FastAPI's default 422 echoes `input` (OCR text). | Use a custom validation handler (paths only). Canary log-capture test. |
| 8 | P2 | DESIGN §7.1 "escalation trigger" vs §4.1 5% vs EVAL-PERF-02 5–15% | Triggers are undefined, so disclosure and cost rest on an unknown. | Define the triggers in §5.2 and plan cost at 10%. |
| 9 | P2 | UI ST-SERVER-ERR/ST-PAUSED vs DESIGN §3.7 + PIPELINE (3 fails → `basic`; 503 basic) | No basic-card state. Unclear whether 503/offline use attempts. A user Retry is a 4th call. | Add ST-BASIC. 503/offline don't count. Rule = "≤3 automatic calls". |
| 10 | P2 | FEATURES F2f "min of its fields", UI "every field grounded" vs DESIGN §5.5 "required fields + class_conf" | ">2 flagged" can't happen. F2f doesn't cover 3+ fields in band. Boundaries unstated. | Adopt the DESIGN wording: Ready ≥0.90, Ask 0.60 ≤ s < 0.90, Needs <0.60. Optional fields below 0.60 → `missing`. |
| 11 | P2 | DESIGN §6.3/Q3 (events: no alarms) vs UI event wireframes with 2 alerts, Settings "Default alerts 2" | Default alerts on events contradict each other. | Presets for deadlines only. Rename the row "Deadline alerts". |
| 12 | P2 | DESIGN §6.4 "alarms ≤ due" vs all-day sample (09:00 on the due date) | The morning-of alert gets dropped for all-day deadlines. | All-day bound = 23:59 local. Add an EVAL-DATE case. |
| 13 | P2 | UI ST-PAST vs DESIGN §5.5 "Past: no action" vs §6.2 "already happened" | Three behaviours. | Blocking date row. Drop "already happened". |
| 14 | P2 | UI ST-SENSITIVE (no card) vs DESIGN §5.5 (manual card) | Contradiction. | UI version plus optional blank [Add manually]. |
| 15 | P2 | UI ST-CATCHUP "[Read them]" vs DESIGN §3.8 auto on open | Auto vs tap. Image toggle scope for catch-up is unclear (UI toggle is Android-only). | Auto-process. `catchup` = auto-detected (opt-in). Show the toggle on iOS. |
| 16 | P2 | UI §4.6 lists NTF-ADDED, UI cut 1, BUILD R-1 vs D19 | Leftover [Add] text. | Delete NTF-ADDED and UI cut 1. Mark R-1 resolved. |
| 17 | P2 | DESIGN §8.5 flows vs UI §7.4/BUILD MAE-* | Different sets. Search (F6c) and onboarding aren't automated. | Cite MAE-*. Add a search step to MAE-UNDO. |
| 18 | P2 | BUILD cuts 6/7/11 vs D15/D18, F2f Accept, F1(b)/EVAL-BAR-12; cut 12 vs FEATURES F6 + UI §7.7 "search cut first" | Cuts break locked acceptance. Search order conflicts. | Mark 6/7/11 "Chair amendment needed". Pick one search position. |
| 19 | P2 | BUILD critical path "16" vs §6 sequential screens + CP1 | It leaves out HOME, READONLY, SETTINGS and THEME→LIB→MOTION. | Recompute (≈20+) and add the graph edges. |
| 20 | P2 | BUILD sizes | EXECUTOR (M: SP-7+SP-8 on 3 devices, fallbacks, reconcile) and ANDROID-WORKER (M: OCR, rules, POST, inbox, notify, SP-2) are effectively L. SP-5/SP-13 have no owner. | Split both. SP-13 → REPO, SP-5 → EVALSET. Re-total. |
| 21 | P2 | D16 (300 ceiling) vs DESIGN §2.2 "internal tracks ≤100" | 300 needs external TestFlight review and a Play closed track. | Update §2.2 and link the official limits. |
| 22 | P2 | DESIGN P5 (Android 14 partial) vs ST-PERM-PHOTOS-LIMITED (iOS-only) | No Android state. | Extend the state. Worker stays off. |
| 23 | P2 | FEATURES F2(a) "source" vs ProposedAction/UI | Never produced. | Map it to the notes footer and say so. |
| 24 | P2 | DESIGN `correction` "never leaves device" vs §7.1 core.db in OS backup; Android `inbox/*.json` | False comment. Inbox isn't in the backup rules or delete-all. | Reword. Exclude and wipe the inbox. |
| 25 | P2 | DESIGN §6.2 reconcile "if not found, write" vs "no action without a tap" | A write can happen days later at next launch. | Write only if <5 min since the tap. Otherwise back to Draft. |
| 26 | P2 | DESIGN §3.8/UI I1–I2 vs P3 | No official doc for a share extension opening its app, and the magic moment depends on it. | Cite Apple docs. SP-3 PASS includes "opens unaided". Fallback: "Saved, open to review". |
| 27 | P3 | `kv.token` plaintext, backed up vs SEC-TOKEN | Weak storage. | expo-secure-store, excluded from backup. |
| 28 | P3 | IDs | QA-PERF is "owned by UI" but not defined there. QA-PERF-06 is missing. EVAL-META-01/02 and EVAL-GROUND-01 are undefined. SP-13–16 aren't in DESIGN §11. S7/S9 are undefined. F2f has no traceability row. Docs cite D1–D18. | Define them and cite D1–D19. |
| 29 | P3 | DESIGN "Already added", restored "image not on this device", 426, 413, intent/system-editor fallback vs UI | No states. | Add ST-ALREADY-ADDED, ST-UPGRADE, ST-RESTORED-MISSING. Extend ST-PERM-CAL-DENIED. |
| 30 | P3 | SP-5 (≤10% / >25%), SP-11 FAIL | The 10–25% band is undefined. SP-11 has no hard fail. | 10–25% → keep escalation. SP-11 fail if p95 >6 s. |
| 31 | P3 | DESIGN "3 attempts (30 s, 5 min, 30 min)" | That's 4 attempts. | "Initial + 2 retries". |
| 32 | P3 | DESIGN "Tue Nov 18", "Fri Nov 21"; UI "Mon, Dec 1"; middle dot; §6.6 copy | Wrong weekdays (they're Wed/Sat/Tue). Copy breaks UI rules. | Fix them. UI copy is the source. |
| 33 | P3 | Unlinked platform claims | Android calendar "one prompt", gorhom a11y, Increase-Contrast API, `calshow:` (undocumented), Play internal ≤100, `eas build --local`, "EAS secrets" (now environment variables), Apple/Pixel claims cite press only. | Link official docs or mark (verify). |
| 34 | P3 | FEATURES F6(b) "embeddings" vs FTS5-only | Stale. | Edit F6(b). |
| 35 | P3 | DESIGN §2.3 "Photos at catch-up" vs UI ONB-4 | Prompt timing differs. | Align on ONB-4. |

No conflict found: 8 s toast; 18:00/09:00 alerts; 0.90/0.60; $25 cap; 100/day; 5/10 s SLO; ≤1 s/≤2 s; FTS5 300 ms; D7 write-only; model never executes; secrets rule; nothing declared above L.
