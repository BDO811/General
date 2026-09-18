# Phase 0 spec lock: Amplifier "Check Engine Light"

Status: locked for Phase 1 build. Decisions below follow the recommendations in
`ARCHITECTURE_PLAN.md` sections 2, 5, and 8. Revisit only if Amit overrides.

## 1. Scope decision (plan section 8, item 1)

**v1 ships as the scheduled micro check-in**, not ambient listening. No background
microphone access anywhere in v1. This is the only version built in Phase 1.
Ambient capture (plan section 6) stays a Phase 2 candidate, gated on legal review
of two-party consent exposure before any engineering work starts on it.

## 2. Sign decision (plan section 8, item 2)

**v1 sign is dehydration**, reusing the integration already proven in Attune
(`POST /v2/signs/dehydration/analyze`). Cognitive-impairment or another
Established-tier sign is the natural Phase 3 addition once available. The
result schema below already carries a `sign` column, so adding a second sign
is additive, not a migration.

## 3. Ship vehicle decision (plan section 8, item 3)

**Standalone app**, not a mode inside Attune, per plan section 4 (native Android
is required for exact-time scheduling, foreground services, and Doze survival;
Attune is Expo/RN). Shares Attune's Supabase project and LAM integration
pattern, not its client codebase.

## 4. Supabase schema for daily results

```sql
create table if not exists public.daily_checks (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  sign          text not null default 'dehydration',
  local_date    date not null,               -- device-local calendar day the check belongs to
  requested_at  timestamptz not null default now(),
  completed_at  timestamptz,
  job_id        text,                        -- Amplifier LAM job id
  level         text,                        -- none/low/consider/moderate/elevated/inconclusive
  score         numeric,
  flagged       boolean not null default false,
  audio_quality_issue text,                  -- set when LAM flags a capture problem; UI shows gray + retry
  status        text not null default 'pending', -- pending/uploading/processing/done/failed
  error_reason  text,
  created_at    timestamptz not null default now(),

  unique (user_id, sign, local_date)
);

create index if not exists daily_checks_user_date_idx
  on public.daily_checks (user_id, local_date desc);

alter table public.daily_checks enable row level security;

create policy "users read own daily checks"
  on public.daily_checks for select
  using (auth.uid() = user_id);

create policy "users insert own daily checks"
  on public.daily_checks for insert
  with check (auth.uid() = user_id);
```

Notes:
- One row per user per sign per local calendar day. The unique constraint is
  what makes "retry within the same day, roll forward rather than stack" (plan
  section 5, Reliability) enforceable at the DB level instead of just in
  client logic.
- `description` / `vocal_features` from the LAM response are never written to
  this table. Per plan section 5, that narrative field is care-staff-only and
  must not reach a consumer-facing store.

## 5. Three screens, roughed out

- **Home**: today's check-engine light (green/yellow/red/gray) + a short trend
  sparkline of the last ~14 days. Primary CTA is "Record today's check" when
  nothing has been submitted yet for the local day; otherwise shows status
  (processing / done / retry needed).
- **History**: reverse-chronological list of past days, light + score only.
  No raw biomarker table, no `vocal_features`. This matches the Oura/WHOOP-style
  single-composite-number pattern called out in plan section 5.
- **Settings**: notification time window, "not a diagnostic device" disclosure
  (re-shown, not just at onboarding), battery-optimization exemption prompt,
  data deletion / account controls.

## 6. Open items still owned by Amit

Everything else in plan section 8 is now locked. The one item that remains
genuinely open is the Phase 2 gate: whether to pursue ambient capture at all,
which per plan section 6 requires actual legal review, not an engineering call.
