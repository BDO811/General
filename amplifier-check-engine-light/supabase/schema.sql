-- Daily results schema for Amplifier "Check Engine Light".
-- Canonical copy lives in docs/PHASE_0_SPEC.md section 4; this file is what
-- actually gets run against the Supabase project (reuses Attune's project
-- per ARCHITECTURE_PLAN.md section 3 rather than standing up a new backend).

create table if not exists public.daily_checks (
  id            uuid primary key default gen_random_uuid(),
  user_id       uuid not null references auth.users(id) on delete cascade,
  sign          text not null default 'dehydration',
  local_date    date not null,
  requested_at  timestamptz not null default now(),
  completed_at  timestamptz,
  job_id        text,
  level         text,
  score         numeric,
  flagged       boolean not null default false,
  audio_quality_issue text,
  status        text not null default 'pending',
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

create policy "users update own daily checks"
  on public.daily_checks for update
  using (auth.uid() = user_id);
