# Amplifier "Check Engine Light" — Android Passive Voice Monitor
Architecture and build plan · September 17, 2026

## 1. Product framing

The product is a single daily signal, not a dashboard. Once a day, near noon, the phone captures a short voice sample and Amplifier's LAM turns it into one status: green, yellow, or red, the same way a check engine light works. The user doesn't log anything. They just carry the phone and talk.

## 2. The passive listening decision

"Listens passively" can mean two very different builds, and this is the one call that decides almost everything downstream, so I'm laying out both.

**Recommended for v1: scheduled micro check-in, not continuous listening.** Around noon, the app fires a local notification and asks for 15 to 30 seconds of speech (a short prompt, or the user just talking). No microphone runs before or after that window. This is "passive" from the user's point of view because there's nothing to log, no symptoms to enter, no data to interpret. It also sidesteps the two problems that would otherwise dominate the build: two-party consent wiretapping law in states like California and Illinois, which requires everyone in a recording to know it's happening, and Google Play's policy against background microphone access outside a clear, disclosed, in-use purpose. A once-a-day, user-triggered, single-party recording of the phone's own owner clears both concerns cleanly.

**True ambient listening (v2, contingent on legal review).** If Amit wants the app running in the background and pulling a sample out of whatever the user happens to be saying near noon, that needs an on-device voice activity detector (VAD) gating a rolling audio buffer that never leaves the device as raw audio, a foreground service with a persistent notification (Android requires this for any background mic use), and a documented consent and disclosure flow that would need actual legal review before ship, not just an engineering decision. I'd build v1 first and revisit this once the sign itself is proven out with real users, rather than taking on the legal and Play Store approval risk before there's a working product to protect.

The rest of this plan assumes v1. The v2 delta is called out separately in section 6.

## 3. High-level architecture

```
[Local notification, ~12:00pm +/- 15min jitter]
        |
        v
[Foreground recording screen] --15-30s clip (WAV/M4A)--> [Encrypted local temp file]
        |
        v
[Backend proxy (Supabase Edge Function)] --multipart--> [Amplifier LAM API]
        |                                                  POST /v2/signs/{sign}/analyze
        |                                                  -> job_id
        v
[Poll GET /v2/jobs/{job_id} until done/failed]
        |
        v
[Result: signal.level, signal.score, flagged] --store--> [Room DB, local history]
        |                                          |
        v                                          v
[Delete temp audio file]                  [Update check-engine-light UI + push result notification]
```

The API key never ships in the APK. The client talks to a thin proxy, which is the only thing holding `X-Account-ID` / `X-API-Key` and calling `api.amplifierhealth.com` directly. Reuse Attune's existing Supabase project for this rather than standing up a new backend, since the account model and edge function pattern are already built and proven (`src/scan/amplifier.ts` in the Attune repo is the reference implementation).

## 4. Why native Android, not Expo/React Native

Attune is Expo/React Native, which is right for a cross-platform scan-on-demand app. It's the wrong foundation for this app specifically, because reliable exact-time scheduling (`AlarmManager.setExactAndAllowWhileIdle`), foreground services, and Doze-mode survival are all native Android APIs that Expo either doesn't expose cleanly or requires ejecting to a custom dev client to reach. Given the whole product hinges on whether the noon check actually fires reliably, I'd build this as a standalone Kotlin app rather than force it into Attune's RN shell. It can still share Attune's Supabase backend, LAM integration pattern, and visual design language.

## 5. Components

- **Onboarding/consent**: mic permission rationale, plain-language data use disclosure, "not a diagnostic device" language up front, before first recording.
- **Scheduler**: WorkManager periodic work as the primary driver, with an exact alarm as backup for the actual noon trigger. A randomized jitter window (11:45am to 12:15pm) avoids everyone hitting the LAM API at the same second and reads less like covert fixed-clock surveillance to Play Store reviewers.
- **Capture**: MediaRecorder-based short clip, mono, 16kHz, matching LAM's recommended format. Runs inside a foreground service with a visible notification for the duration of the recording only.
- **Local storage**: Room for scores and history metadata. Jetpack Security EncryptedFile for the raw clip during the brief window between recording and upload, deleted immediately on a successful LAM response, and on any failure after the retry window closes.
- **Network layer**: Retrofit/OkHttp to the Supabase proxy. Proxy forwards to `POST /v2/signs/{sign}/analyze`, returns `job_id` to the client, or completes the poll server-side and pushes via FCM once done, which is the better long-run pattern since it doesn't need the app in the foreground to finish the job.
- **Sign selection for v1**: dehydration. It's the sign already live and proven in Attune, so the integration risk is close to zero. Cognitive-impairment is listed as a future Established-tier sign and is a natural v2 addition once available.
- **Result handling**: store level (none/low/consider/moderate/elevated/inconclusive), score, and flagged per day. The check-engine light maps green to none/low, yellow to consider/moderate, red to elevated, gray to inconclusive or a flagged audio_quality issue, telling the user to retry rather than showing a false reading. Only ever show level/score-derived numbers in the UI. The description/vocal_features narrative field from the API is care-staff-only per Amplifier's own compliance posture and should never reach the consumer screen.
- **UI**: one home screen (today's light plus a short trend line), one history screen, one settings screen. Nothing else. The competitive research on Oura/WHOOP/Garmin scores says users respond to a single composite number they can watch move over time, not a wall of raw biomarkers, and this product should follow that pattern rather than Attune's more clinical scan-report layout.
- **Reliability**: prompt the user once to exclude the app from battery optimization, since Doze mode is the single most common reason a scheduled Android task silently stops firing. Retry within the same day on failure or offline, roll to the next day rather than stacking missed checks.

## 6. v2 delta (ambient passive capture, legal-gated)

If Amit later wants true background listening instead of the noon prompt: add a PassiveListenService foreground service running a lightweight on-device VAD (Silero VAD via ONNX Runtime Mobile is the standard choice here), which gates a small rolling buffer and discards anything that isn't voice within seconds. Raw audio never persists past that rolling window. At the scheduled time, the best segment from the buffer gets submitted the same way the v1 clip does. This needs a real consent and disclosure review before it ships, not an engineering sign-off, since the two-party consent question changes the moment the app might capture someone other than the phone's owner.

## 7. Build phases

- **Phase 0 (about 1 week)**: lock the spec, pick the sign, confirm the Supabase schema for daily results, rough out the three screens.
- **Phase 1 / MVP (3 to 4 weeks)**: native Android app, scheduled noon prompt, manual short recording, Supabase proxy plus LAM integration, check-engine-light home screen, history, completion notification.
- **Phase 2 (4 to 6 weeks, only after v1 has real usage)**: ambient VAD capture per section 6, Doze/background hardening, Play Store policy pre-review.
- **Phase 3**: second sign once cognitive-impairment or another Established-tier sign is available, longer trend views, export/share for a care team.

## 8. Open items for Amit

- Confirm v1 scope (scheduled prompt) versus committing straight to v2 (ambient) knowing the legal review v2 requires.
- Confirm dehydration as the v1 sign, given it's the one already integrated in Attune.
- Decide whether this ships as a new standalone app listing or a mode inside Attune itself.
