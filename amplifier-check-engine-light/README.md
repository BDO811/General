# Amplifier "Check Engine Light": Android

Native Kotlin/Compose implementation of the Phase 1 MVP described in
`ARCHITECTURE_PLAN.md`, with the Phase 0 decisions it left open locked in
`docs/PHASE_0_SPEC.md`: v1 ships as the scheduled noon micro check-in (no
ambient listening), the sign is dehydration, and this is a standalone app
sharing Attune's Supabase project rather than a mode inside Attune.

## Layout

```
app/                                    Android app module
  src/main/java/com/amplifierhealth/checkenginelight/
    scheduler/     WorkManager periodic job, exact-alarm backup, boot receiver
    capture/       Foreground recording service
    audio/         MediaRecorder wrapper and encrypted temp storage
    data/          Room (local history), Retrofit (Supabase proxy), repository
    notification/  Reminder, recording, and result notification channels
    model/         SignalLevel: the only vocabulary the UI is allowed to show
    ui/            Onboarding, home, history, settings, recording screens
supabase/
  schema.sql                            daily_checks table (RLS-scoped per user)
  functions/amplifier-proxy/index.ts    holds the LAM account credentials;
                                        the client never sees them
docs/
  PHASE_0_SPEC.md                       locked scope/sign/schema decisions
```

## What's implemented

- Scheduler: WorkManager periodic work jittered to the 11:45am-12:15pm
  window, plus an exact-alarm backup for devices that defer WorkManager past
  it, plus boot re-arming. Neither path touches the mic; both only post the
  reminder notification.
- Capture: a foreground service owns the mic for one 15-30s clip, started
  only by explicit user action from the recording screen.
- Storage: the raw clip is encrypted at rest (Jetpack Security `EncryptedFile`)
  between recording and upload, and deleted on success or on terminal
  failure. Only derived level/score persist in Room.
- Network: client talks only to the Supabase edge function proxy; the proxy
  is the sole holder of the Amplifier account credentials and is also where
  the `description`/`vocal_features` narrative fields get stripped before
  anything reaches the client.
- UI: home (today's light plus a 14-day trend), history, settings, onboarding,
  recording. No raw biomarker views anywhere.

## What's still open (not guessed at here)

- **Auth flow.** `NetworkModule.AuthTokenProvider` is a stub. The plan
  doesn't specify how this app authenticates to Supabase (anonymous device
  auth vs. a lightweight sign-in), and that's a product decision, not
  something to default silently.
- **Proxy base URL / Supabase project ref.** `NetworkModule.PROXY_BASE_URL`
  is a placeholder; point it at the actual Attune Supabase project before
  running this against real data.
- **App icon / brand assets.** Placeholder vector icons only.
- Everything in `ARCHITECTURE_PLAN.md` section 6 (ambient v2) is untouched.
  It's legal-gated, not an engineering task.

## Building

Requires the Android SDK (not present in the environment this was scaffolded
in, so this hasn't been compiled; review before trusting it end to end).
Standard Gradle build once the SDK is available:

```
./gradlew :app:assembleDebug
```
