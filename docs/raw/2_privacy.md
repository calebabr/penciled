# Round 2 - Privacy and Security Design (design only)

Scope: FEATURES.md F1-F8 as locked. Control IDs are stable (SEC-*). Provider retention terms and store-form wording change often; every external claim below must be re-verified at build time (links given). Not legal advice.

## 1. Data minimization
Principle: on-device first, send the least that achieves the proposal, never send what the guard flags.

- **SEC-MIN-TEXT (default path): on-device OCR, upload text only.** iOS Vision / Android ML Kit run locally. The proxy receives OCR text plus capture time and timezone (needed for F3), never the pixels. Tradeoff: text-only is far smaller and cheaper, removes faces, photos, QR codes and visual metadata, and is easier to redact. It loses layout (flyers, tables, group-chat sender attribution) and stylized fonts. 
- **SEC-MIN-IMAGE (fallback, opt-in per item):** when OCR confidence is low or the class looks layout-dependent, offer "Send image for better reading". The image is downscaled (long edge ~1280 px), re-encoded to strip EXIF/GPS, and sent only after the sensitive guard passes. Beta default: image upload OFF; enable by a visible setting so the disclosure is honest.
- **SEC-REDACT (before any upload):** deterministic regex/checksum redaction on OCR text: card numbers (Luhn), SSN/ID patterns, IBAN, emails, phone numbers not needed for an event, long digit runs, OTP-like 4-8 digit codes, URLs with tokens. Replace with typed placeholders ([CARD], [EMAIL]). Redaction runs on device; the server never sees originals. For images, redaction means blur of OCR-box regions matching those patterns (post-beta; in beta, image upload is simply blocked if any pattern hits).
- **SEC-NOID:** no account email/name in LLM calls; the proxy sends a rotating opaque request ID only. Embeddings (F6): compute on device if feasible; if server-side, embed redacted text only.
- Not sent, ever: contacts, photo-library metadata, device identifiers other than the per-install token, the full library (only the single screenshot being processed).

## 2. Encryption
- **SEC-TLS:** TLS 1.2+ (prefer 1.3) to the proxy only; ATS on iOS, `usesCleartextTraffic=false` on Android. Certificate pinning is optional and risky for a solo dev (rotation outages); use pin-to-intermediate with a backup pin or skip in beta.
- **SEC-REST-DEVICE:** local DB (screenshots, OCR text, embeddings) in app sandbox with iOS Data Protection `completeUntilFirstUserAuthentication` and Android EncryptedFile / SQLCipher with a Keystore-held key. Auto-backup excluded for the screenshot cache (`allowBackup` rules / `isExcludedFromBackup`) so text does not leak to cloud backups unexpectedly.
- **SEC-REST-SERVER:** managed Postgres/object storage with provider-managed AES-256 at rest. Beta stores only: opaque user ID, action metadata, redacted text only if the user enables cross-device sync. Default: server stores no screenshot content after the LLM call returns (see SEC-RETAIN).
- **SEC-KEYS-SERVER:** provider and DB secrets only in the host's secret manager, rotated on any suspicion; never in the repo or client.

## 3. Sensitive screenshots
Locked requirement (F7b): sensitive screens are not sent and get no cloud proposal.

- **SEC-GUARD (two-stage, fail closed):**
  1. *On-device pre-OCR cheap check:* source-app signals where the platform exposes them (banking/password-manager/health bundle IDs on Android foreground package; not available on iOS), plus FLAG_SECURE-style hints.
  2. *On-device text classifier after OCR:* keyword and pattern scoring (account/routing number, "balance", "password", "CVV", "SSN", "diagnosis", "prescription", "passport", driver-license layouts, OTP messages, message-thread UI heuristics such as many short left/right bubbles with names). Score above threshold = sensitive.
- **SEC-LOCALONLY:** sensitive result means: no network call, stored locally only, labeled "Kept on this phone", library search still works locally (local keyword index), no cloud proposal. Rationale for keep-local over drop: users still want to find it; skip-entirely loses library value; the screenshot never leaves either way.
- **SEC-GUARD-BIAS:** thresholds favor false positives (a skipped flyer is cheap; a leaked bank page is not). Beta instrumentation counts guard rate only. Per-item override "Send anyway" is allowed for non-ID/financial classes only and logged as a count.
- Limits to state honestly: a keyword guard misses unusual layouts and non-English content; it is a mitigation, not a guarantee. Disclose this in onboarding (SEC-DISCLOSE).
- **SEC-DISCLOSE:** onboarding states plainly what is sent, to whom (named LLM provider), and for how long, before any permission request (F7a).

## 4. API key protection and abuse control
- **SEC-NOKEY:** zero third-party provider keys in the app binary or remote config. The app only knows the proxy URL.
- **SEC-PROXY:** a stateless backend proxy (serverless fits a solo dev) holds the LLM key, builds the system prompt server-side (clients cannot supply system prompts or tools), enforces a model allowlist, max input size and max output tokens, and returns only schema-constrained JSON.
- **SEC-ATTEST:** device/app integrity at token issuance: iOS App Attest (DeviceCheck), Android Play Integrity API (standard request with a server-supplied nonce). Verified server-side; failures get a reduced quota rather than a hard block (attestation is a signal, not proof; rooted/jailbroken and sideloaded testers exist). Docs: https://developer.apple.com/documentation/devicecheck/establishing-your-app-s-integrity and https://developer.android.com/google/play/integrity
- **SEC-TOKEN:** after attestation the proxy mints a short-lived (e.g. 1 h) signed token bound to a per-install ID; refresh requires a fresh assertion periodically. Revocable per install. Beta testers additionally need an invite code.
- **SEC-RATE:** per-install and per-IP limits (e.g. 60 requests/hour, 300/day beta), global daily spend cap with a kill switch, anomaly alerts. At 1M users, add per-user tiers and queueing. A leaked token costs at most one install's quota.
- **SEC-AUTH-FUTURE:** accounts (Sign in with Apple / Google) before sync features; Apple requires Sign in with Apple when other third-party sign-in is offered.

## 5. Logging
- **SEC-LOG-NOCONTENT:** servers and clients never log request bodies, OCR text, images, model output, or extracted fields. Allowed: request ID, install ID hash, timestamp, status code, latency, token counts, model name, class label, guard/outcome enums.
- **SEC-LOG-SCRUB:** disable body logging in the host/CDN/APM by default; crash reporters configured with no breadcrumbs of UI text; analytics events (F8) use a fixed enum schema with no free-text fields. Add a CI test that greps for logging of known payload fields.
- Log retention 14-30 days; access limited to the developer.

## 6. Retention and provider settings
- **SEC-RETAIN:** the proxy is pass-through: screenshot text/image held in memory only for the call, then discarded. Nothing about content persisted unless the user enables sync (then redacted text and fields, deletable).
- **SEC-PROVIDER:** use only a paid/API tier, never a consumer or free tier that trains on inputs. Select the provider's zero-data-retention or shortest-retention option where available and confirm in writing; record the chosen provider and terms in the privacy policy. Verify current terms: OpenAI API data controls https://platform.openai.com/docs/guides/your-data ; Anthropic commercial retention https://privacy.claude.com ; Google Gemini API terms (free tier may use data for product improvement) https://ai.google.dev/gemini-api/terms . Typical API norms are short abuse-monitoring retention (about 30 days) unless a ZDR agreement exists; a solo dev may not qualify, so disclose the actual period rather than claiming zero retention.
- **SEC-DPA:** sign the provider DPA / accept data-processing terms, list the provider as a subprocessor.

## 7. User deletion
- **SEC-DEL-ONE:** deleting a screenshot removes the local record, embedding, and any server-side synced record; issues a signed delete request keyed by the item ID.
- **SEC-DEL-ALL:** "Delete all my data" wipes local DB and files, calls the proxy to delete all rows by install/user ID, revokes tokens, and resets the install ID. Server deletion completes within 30 days at the latest; backups age out and the policy says so. Acceptance test (F7d): seed N items, delete, assert zero rows and zero objects by direct query.
- **SEC-DEL-ACCT:** once accounts exist, in-app account deletion is mandatory on both stores: https://developer.apple.com/support/offering-account-deletion-in-your-app/ and https://support.google.com/googleplay/android-developer/answer/13327111 . Deleting a calendar event previously created is separate (Undo), not part of data deletion.
- **SEC-EXPORT:** a simple JSON export of the action log (low cost, supports access rights).

## 8. Store disclosures (must match actual behavior; mismatch risks rejection)
- **Apple App Privacy label:** https://developer.apple.com/app-store/app-privacy-details/ . Likely declarations: User Content > Photos or Videos (if image upload exists) and Other User Content (OCR text) as collected, linked to the user only if an ID/account is used, purpose App Functionality, not used for tracking; Identifiers > Device ID if the per-install ID persists; Diagnostics (crash data) if used. Data sent to a third-party LLM counts as collected even when transient, unless it meets Apple's limited exceptions (processed only on-device or not retained in readable form); do not rely on the exception. Provide a privacy policy URL and a Privacy Manifest (PrivacyInfo.xcprivacy) covering required-reason APIs.
- **Google Play Data safety:** https://support.google.com/googleplay/android-developer/answer/10787469 . Declare Photos and videos, and "Other user-generated content / App activity" as collected and shared with a service provider (the LLM host is a processor; Play treats service-provider transfers as "collected" but excludes them from "shared" under its processing exception); encrypted in transit: yes; deletion request mechanism: yes (in-app plus web link). Also complete the sensitive-permission declarations: READ_MEDIA_IMAGES now has restrictions (https://support.google.com/googleplay/android-developer/answer/14115180); prefer the Photo Picker / limited access, which also supports minimization.
- **SEC-STORE:** a checklist item in release: re-derive both forms from the actual network calls before every submission.

## 9. Threat list
| ID | Threat | Mitigation |
|---|---|---|
| T1 | **Prompt injection in screenshot** (text in image or chat says "ignore previous, create event X / email Y") | See below. SEC-INJ |
| T2 | Provider key theft from the app | SEC-NOKEY, SEC-PROXY |
| T3 | Abuse of proxy / cost drain by a modified client | SEC-ATTEST, SEC-TOKEN, SEC-RATE, spend cap |
| T4 | Sensitive content leaves device | SEC-GUARD, SEC-REDACT, SEC-LOCALONLY, SEC-DISCLOSE |
| T5 | Logs leak content | SEC-LOG-NOCONTENT, SEC-LOG-SCRUB |
| T6 | Device loss / local data theft | SEC-REST-DEVICE, OS lock screen; optional app lock (post-beta) |
| T7 | Backup/cloud leak of local DB | backup exclusion |
| T8 | Model output exfiltration via links/markdown | render fields as plain text; never auto-open URLs; only show fields not free HTML |
| T9 | Supply chain / SDK telemetry | minimal SDKs, audit each for data collection; list them in store forms |
| T10 | Deletion not truly deleting | SEC-DEL-* with automated test |
| T11 | Insider/solo-dev account compromise | MFA on cloud, hosting, store and provider accounts; least-privilege tokens |

**SEC-INJ (prompt injection) design.** The model is untrusted input handler, never an actor:
1. **SEC-INJ-NOTOOLS:** the model has no tools, no network, no memory of other screenshots, and cannot read the library. Its only output is a JSON object validated against a strict schema (class enum, typed fields). A malicious instruction therefore has no channel to do anything except alter the proposed fields.
2. **SEC-INJ-VALIDATE:** deterministic code re-parses every field: dates resolved by F3 code, ranges and year sanity (e.g. within -1 to +2 years), title length and character limits, no URLs/commands in title, max 3 actions, allowed action types only (calendar event, reminder). Unknown keys dropped. Fields absent from the OCR text (substring/fuzzy check against the source text) are flagged as "not found in screenshot".
3. **SEC-INJ-CONFIRM:** nothing executes without a user tap on a card showing every field (F4a). Injection can at worst create a wrong-looking proposal the user sees and dismisses. No attendee invitations or messages are sent in beta (no outbound side effects), so an injected "invite everyone" has no effect.
4. **SEC-INJ-ISOLATE:** screenshot text is delimited and labeled as data in the prompt; instructions only in the server-built system prompt. This reduces but does not eliminate success; layers 1-3 carry the guarantee. Add injection test fixtures (screenshots containing "ignore instructions", fake system prompts) to the eval set and track the rate of schema/validation rejections.
Reference: https://genai.owasp.org/llmrisk/llm01-prompt-injection/

## 10. Beta priorities (solo dev)
Must before first tester: SEC-NOKEY, SEC-PROXY, SEC-TOKEN (invite code + rate limit), SEC-TLS, SEC-LOG-NOCONTENT, SEC-GUARD (v1 keyword), SEC-REDACT (text), SEC-INJ-*, SEC-DISCLOSE, SEC-DEL-ONE/ALL, SEC-PROVIDER (paid tier, retention documented), SEC-STORE. Before wider release: full SEC-ATTEST, spend cap automation, image redaction, account deletion, SEC-EXPORT.
