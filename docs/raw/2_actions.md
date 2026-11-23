# Round 2: Action engine design (beta: 3 actions)

Principle: model proposes (a typed `Proposal` JSON), deterministic code validates and executes, user confirms. The executor never receives free text from the model, only validated typed fields. Doc links are official pages from my knowledge, not re-fetched this session; verify before build.

Action IDs: **ACT-CAL-CREATE** (calendar event), **ACT-REM-CREATE** (reminder), **ACT-LAD-CREATE** (deadline-ladder reminder set). Each has an undo path, logged as `*-UNDO`.

## 0. Shared machinery (applies to all three)

**State machine per proposal:** `proposed -> editing -> confirming -> executing -> done | failed`; `done -> undone | undo_blocked`. Only `confirming` is entered by a user tap. `failed` keeps the proposal and its edits.

**Idempotency core.** Each proposal gets a client UUID `actionId` at creation (not at tap). Executor does, inside one serialized actor/queue per actionId:
1. Disable the Confirm button on first tap (UI guard).
2. Look up `actionId` in the local ledger (SQLite). If status `done`, return the stored result without writing. If `executing` and the process died, run the *reconcile* step: search the platform store for the marker (below); if found, adopt it as done; if not, proceed.
3. Write platform item carrying the marker; persist platform ID + fingerprint in the same transaction as status `done`.

**Marker** (lets us find our items after crash/retry): iOS: `EKEvent.url = shotact://a/<actionId>` for events (Reminders: put marker in `notes` footer, URL on EKReminder also works on iOS 17 but keep notes as the fallback). Android: `CalendarContract.Events.CUSTOM_APP_PACKAGE` + `CUSTOM_APP_URI = shotact://a/<actionId>`.

**Fingerprint:** SHA-256 of the canonical written fields (title, start, end, tz, location, alarms) plus the item's `lastModifiedDate` (iOS) / `LAST_DATE`/`DIRTY` state (Android) read right after write. Used for undo-after-edit detection.

**Common validation (code, before the confirm button enables):** title non-empty after trim, 1..200 chars, control characters stripped; any field flagged `needs_review` must be touched or explicitly acknowledged; all datetimes resolved by F3 code into (local date, time, IANA tz) and shown with the assumption note; end > start; duration <= 14 days; start not more than 10 years out; no past start unless user ticks "yes, this already happened" (events) / reminders never in the past (hard rule). Location <= 300 chars, plain text only. Source note appended: "Added from screenshot <date>" (no screenshot content beyond extracted fields).

**Edit-before-confirm sheet (shared):** all fields are editable; flagged fields highlighted and sorted first; Confirm shows a one-line summary ("Fri Nov 21, 7:00 PM-9:00 PM, America/Chicago -> Calendar: Home"); edits mutate the typed Proposal, re-run validation live; Cancel/swipe-away = no side effects, proposal stays in the feed as `dismissed`.

**Action log (append-only, local SQLite; counts-only export for F8).**
```
action_log(
  log_id TEXT PK, action_id TEXT, act TEXT,        -- ACT-CAL-CREATE | ACT-REM-CREATE | ACT-LAD-CREATE | *-UNDO
  ladder_id TEXT NULL, rung INT NULL,
  screenshot_id TEXT, proposed_json TEXT,           -- model output as proposed
  confirmed_json TEXT,                              -- fields as user confirmed
  edited_fields TEXT,                               -- JSON array of field names changed (F8)
  platform TEXT, backend TEXT,                      -- ios|android ; eventkit|calendarprovider|ics|local_notif
  store_access TEXT,                                -- full|write_only|none|intent_ui
  platform_item_id TEXT, calendar_id TEXT, marker TEXT, fingerprint TEXT,
  status TEXT,                                      -- done|failed|undone|undo_blocked|dismissed
  error_code TEXT, error_detail TEXT,               -- enum + redacted
  created_at INT, confirmed_at INT, executed_at INT, undone_at INT NULL, ms_confirm_to_done INT)
```
Content columns stay on device; only counts/rates leave (F8). "Delete my data" wipes rows.

**Error code enum:** `PERM_DENIED, PERM_RESTRICTED, PERM_WRITE_ONLY_NO_UNDO, NO_WRITABLE_CALENDAR, STORE_SAVE_FAILED, STORE_UNAVAILABLE, VALIDATION_FAILED, ALREADY_DONE, ITEM_NOT_FOUND, ITEM_MODIFIED, SYNC_PENDING`.

**Permission principle:** ask just in time at first Confirm (not onboarding), after a one-screen rationale ("so we can add the event and remove it if you tap Undo"). Denied: keep proposal, show "Open Settings" + the .ics fallback ("Add via share sheet instead"). Never re-prompt in a loop; iOS shows the system prompt once, so rationale screen comes first.

---

## 1. ACT-CAL-CREATE: calendar event

### APIs
**iOS: EventKit.** [EKEventStore](https://developer.apple.com/documentation/eventkit/ekeventstore), [Accessing the event store](https://developer.apple.com/documentation/eventkit/accessing-the-event-store), [WWDC23 "Discover Calendar and EventKit"](https://developer.apple.com/videos/play/wwdc2023/10052/).
- iOS 17+: `requestWriteOnlyAccessToEvents(completion:)` (Info.plist `NSCalendarsWriteOnlyAccessUsageDescription`) vs `requestFullAccessToEvents(completion:)` (`NSCalendarsFullAccessUsageDescription`). Write-only can add events but cannot read any events back, including ours. (I'm fairly but not fully certain write-only cannot fetch or delete our own events by identifier; spike-test on a device.)
- Pre-iOS 17: `requestAccess(to: .event)` with `NSCalendarsUsageDescription`; same full capability.
- **Decision:** request **full access** by default, because Undo, reconcile-after-crash, and the edit-detection all need read. If the user grants write-only (or we choose it for a privacy-minimal mode), the create works, but Undo is replaced by "Open Calendar to delete" and duplicate reconcile is disabled; ledger-only idempotency remains. Log `store_access`.
- Calendar choice: `store.defaultCalendarForNewEvents`; if nil or `allowsContentModifications == false`, pick first writable calendar from `calendars(for: .event)` (requires read; under write-only use default only); let user switch calendars in the sheet.
- Fallback A (no permission needed): `EKEventEditViewController` (EventKitUI) presented pre-filled; runs out of process on iOS 17+; user taps Save in Apple's UI. Result: no reliable handle, so no undo. Offered when permission denied.
- Fallback B: `.ics` file (RFC 5545 [spec](https://www.rfc-editor.org/rfc/rfc5545)) via share sheet / `UIActivityViewController`; works for any calendar app; no undo.

**Android: CalendarContract.** [CalendarContract.Events](https://developer.android.com/reference/android/provider/CalendarContract.Events), [Calendar provider overview](https://developer.android.com/identity/providers/calendar-provider), [Permissions](https://developer.android.com/guide/topics/permissions/overview).
- Primary: direct provider insert after the app's own confirm sheet. Needs runtime `READ_CALENDAR` + `WRITE_CALENDAR` (same group, one prompt). Read is needed to list calendars and to find/undo our event.
- Fallback A: `Intent(ACTION_INSERT, Events.CONTENT_URI)` with `EXTRA_EVENT_BEGIN_TIME` etc. ([guide](https://developer.android.com/identity/providers/calendar-provider#intents)); no permission, user saves in their calendar app; no handle back, no undo.
- Fallback B: `.ics` via `ACTION_VIEW`/share with `text/calendar`, `FileProvider`.
- Google Calendar REST API ([events.insert](https://developers.google.com/calendar/api/v3/reference/events/insert)): not used in beta. It would give true idempotency via client-supplied `id` (409 on duplicate) and needs OAuth scope `calendar.events` (a sensitive scope, requires Google verification, sign-in friction). Revisit post-beta for Google-account users.

### Fields
Required: `title`, `start` (date+time+tz) *or* `start_date` with `all_day=true`. Optional: `end` (default start + 60 min, shown as an assumption; all-day = single day), `location`, `notes` (source line), `calendar_id`, `alert` (default none on events; the ladder owns alerts; optional single alert offered, default 30 min before), `url` (marker).
Android mandatory provider columns: `CALENDAR_ID`, `DTSTART`, `DTEND` (or `DURATION`), `EVENT_TIMEZONE` (all-day events must be UTC midnight-to-midnight with `EVENT_TIMEZONE="UTC"`), `TITLE`.

### Validation (code)
Common rules above, plus: all-day events never carry a time; if tz missing from screenshot, use device tz and flag "Assumed your timezone"; if AM/PM ambiguous (1-12 with no marker) the field stays flagged and Confirm is blocked until picked; recurrence is **not** supported in beta (a flagged "repeats?" note is shown; user adds it in their calendar).

### Execution
iOS: `EKEvent(eventStore:)`, set fields, `event.url = marker`, `try store.save(event, span: .thisEvent, commit: true)`, read back `eventIdentifier`/`calendarItemIdentifier`. Android: `ContentResolver.insert(Events.CONTENT_URI, values)` -> URI -> `_ID`; run on `Dispatchers.IO`.

### Idempotency
Ledger check + marker reconcile (section 0). Android reconcile: query `Events` where `CUSTOM_APP_URI = ?`. iOS reconcile: `predicateForEvents` over start-12h..end+12h, filter by `url`. Double-tap: UI disable + per-actionId actor; second call returns stored result.

### Undo
Toast Undo (10 s) and History list. Steps: load ledger row; fetch item by stored ID (iOS also falls back to marker search because `eventIdentifier` can change after calendar sync; Android by `_ID`, falling back to marker). Not found -> mark `undone` with note "already removed". Found: recompute fingerprint of current fields. **Equal** -> delete (`store.remove(event, span:.thisEvent, commit:true)` / `ContentResolver.delete`), status `undone`. **Differs** (user edited it afterward, or attendees added) -> do not delete silently: dialog "You changed this event after we added it. Delete it anyway / Keep it". Keep -> status `undo_blocked`, ledger marks `released` (we no longer manage it). Under write-only / intent UI: no undo; History shows "Added (can't undo from here)" with a deep link to open the calendar app.

### Failure messaging
| Case | Message | Behavior |
|---|---|---|
| Permission denied | "Calendar access is off. Turn it on in Settings, or add this using the share sheet." | Keep proposal, offer Settings + .ics |
| No writable calendar | "No calendar can accept new events. Pick another or add via share sheet." | calendar picker |
| Save throws | "Couldn't add the event. Nothing was changed. Try again." | status `failed`, retry safe (marker reconcile prevents dupes) |
| Sync pending / cloud calendar offline | Added locally; "May take a moment to appear on other devices" | status `done` |

---

## 2. ACT-REM-CREATE: reminder

### APIs
**iOS: EventKit Reminders.** [EKReminder](https://developer.apple.com/documentation/eventkit/ekreminder), [requestFullAccessToReminders](https://developer.apple.com/documentation/eventkit/ekeventstore/4162272-requestfullaccesstoreminders). Reminders have **no write-only tier**; full access only (`NSRemindersFullAccessUsageDescription`, iOS 17+; older `NSRemindersUsageDescription`). Save with `calendar(for:)`/`defaultCalendarForNewReminders()`, `dueDateComponents` (include year/month/day/hour/minute/tz so it is not floating), and an `EKAlarm(absoluteDate:)` via `addAlarm` (due date alone does not notify at a time in all cases; always add the alarm). Fallback: app-local `UNUserNotificationCenter` notification ([docs](https://developer.apple.com/documentation/usernotifications/unusernotificationcenter)) labelled "Reminder from this app only"; (Reminders.app has no VTODO import path via .ics worth relying on).

**Android: there is no system reminders provider.** Options: (1) **Calendar event with a `Reminders` alarm** ([CalendarContract.Reminders](https://developer.android.com/reference/android/provider/CalendarContract.Reminders), `METHOD_ALERT`, `MINUTES`=0): chosen default, same permissions and undo as ACT-CAL-CREATE; the item is a 15-minute event titled "Reminder: ..." so alerts fire from the user's calendar app. (2) App-owned: `AlarmManager.setExactAndAllowWhileIdle` + notification, needing `POST_NOTIFICATIONS` (Android 13+, [docs](https://developer.android.com/develop/ui/views/notifications/notification-permission)) and `SCHEDULE_EXACT_ALARM`/`USE_EXACT_ALARM` ([docs](https://developer.android.com/develop/background-work/services/alarms/schedule#exact-permission)); must reschedule after reboot via `BOOT_COMPLETED`; used as the fallback when calendar permission is denied. (3) Google Tasks API ([tasks.insert](https://developers.google.com/tasks/reference/rest/v1/tasks/insert)): due is date-only (time ignored), so poor for timed reminders; defer.

### Fields
Required: `title`, `due` (date; time optional). Optional: `notes`, `list_id`, `priority` (not set unless extracted), `alert_time` (default = due time; date-only default 09:00 local, flagged "Assumed 9:00 AM").

### Validation
Common rules, plus: alert instant must be > now + 60 s, else block with "That time has passed. Pick a new time." (hard rule from F5); date-only due allowed but alert time always concrete; title is imperative-trimmed ("Submit form") but never rewritten by the model after confirm.

### Execution
iOS: `EKReminder(eventStore:)`, `calendar`, `title`, `dueDateComponents`, `addAlarm`, notes carries marker footer `[shotact:<actionId>]`, `save(reminder, commit:true)`. Android: Events.insert (+`Reminders.insert` with `EVENT_ID`) in one `applyBatch` (`ContentProviderOperation`, with back-reference) so event and alarm land together or not at all.

### Idempotency
Ledger + marker. iOS reconcile: `predicateForReminders(in:)` async fetch, match notes marker. Android reconcile: `CUSTOM_APP_URI`. Local-notification fallback uses `UNNotificationRequest.identifier = actionId` so rescheduling replaces, never duplicates.

### Undo
Same flow as events. iOS: `store.remove(reminder, commit:true)`; if `isCompleted` is true or `title`/`dueDateComponents` differ from fingerprint -> "You changed or completed this reminder. Delete anyway / Keep it". Completed reminders: default Keep. Android: `applyBatch` delete event (alarm cascades). Local fallback: `removePendingNotificationRequests(withIdentifiers:)` / `AlarmManager.cancel`.

### Failure messaging
Denied: "Reminders access is off. Turn it on in Settings, or set an in-app reminder (it only alerts from this app)." Android exact-alarm not granted: "Android is limiting exact alarms; this reminder may be a few minutes late." (inexact scheduling shown honestly). Save failure: same as events, retry-safe.

---

## 3. ACT-LAD-CREATE: deadline-ladder reminder set

A ladder is up to 3 reminders created by ACT-REM-CREATE logic under one `ladderId`; it is one confirm tap but N logged rows.

### Rung rules (pure code, tested table)
Input: deadline instant D (date-only deadline -> D = 23:59 local, flagged), now, user tz. Presets:
- **R1 day-before:** (D.date - 1 day) at 18:00 local.
- **R2 morning-of:** D.date at 08:00 local (if D has a time earlier than 09:00, use D - 3 h).
- **R3 lead-time:** D - 2 h (only if D has a real time; skipped for date-only).
Then: drop any rung <= now + 60 s; drop rungs within 30 min of another (keep the later); if all dropped, offer a single "Remind me now-ish" option at now + 15 min or tell the user "Deadline is too soon for a ladder". DST handled by building rungs from local wall-clock components, never by adding 86,400 s; test across spring-forward/fall-back.

### Fields
Required: `deadline` (as above), `title`. Optional: per-rung enable toggles and editable times (steppers or picker); `notes`. Each rung title: "<title> (due tomorrow)", "(due today)", "(due in 2 h)", generated from a code template, not the model.

### Validation
Per-rung: common rules + not in past + rung <= D. At least one rung enabled to confirm. Rungs must be ordered ascending; edits that reorder or exceed D are rejected inline.

### Execution
Same backend as ACT-REM-CREATE. Atomic where possible: Android single `applyBatch`; iOS save each reminder with `commit:false` then one `store.commit()`; on thrown error call `store.reset()` and roll back. Local-notification fallback registers all rungs, then verifies via `getPendingNotificationRequests`.

### Idempotency
Per-rung marker `<actionId>#r1|r2|r3`; ladder row `done` only if all enabled rungs present. On retry, reconcile creates only the missing rungs (partial-success repair), never duplicates.

### Undo
One Undo removes the whole ladder; each rung runs the ACT-REM undo check independently. Rungs already fired are simply deleted. Edited/completed rungs prompt once as a group: "2 of 3 reminders were changed. Delete all / Keep changed ones". Partial outcome logged per rung (`undone` vs `undo_blocked`).

### Failure messaging
Partial failure: "Added 2 of 3 reminders. The 8:00 AM one didn't save. Retry that one." (retry targets only the missing rung). Permission/notification-disabled: same as ACT-REM-CREATE, plus "Notifications are off for the Reminders app; alerts won't sound" when `UNUserNotificationCenter` or system settings show them disabled (check on the app's own notifications only; for Reminders.app we can only show a hint).

### Reliability test (F5 acceptance)
On-device matrix before ship: create ladder with rungs 2/5/10 minutes out on iOS (Reminders alert) and Android (Doze on, battery saver on); record fire latency; ship messaging if p95 latency > 2 min on Android calendar alarms.

---

## Open items for the red team
1. Write-only vs full access: confirm on device that write-only cannot fetch/delete our own events (drives whether Undo is possible in that mode).
2. `eventIdentifier` stability across sync: confirm fallback marker search is fast enough with large calendars (bound the predicate window).
3. Android OEM calendar apps (Samsung) honoring `CUSTOM_APP_URI` and Reminders alarms.
4. Whether `EKEventEditViewController` returns a usable identifier on iOS 17+ remote UI (would enable undo for the no-permission path).
