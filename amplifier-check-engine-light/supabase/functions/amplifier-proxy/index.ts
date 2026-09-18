// Supabase Edge Function: the only thing holding the Amplifier LAM account
// credentials (ARCHITECTURE_PLAN.md section 3). The Android client never
// sees X-Account-ID / X-API-Key. It authenticates to this function with
// its own Supabase session token, and this function talks to
// api.amplifierhealth.com on the user's behalf.
//
// Routes (relative to the function's own base URL):
//   POST /signs/:sign/analyze   multipart audio -> { job_id }
//   GET  /jobs/:jobId           -> { job_id, status, signal?, audio_quality_issue?, error? }
//
// Deliberately strips `description` / `vocal_features` from every response
// before it reaches the client: those fields are care-staff-only per
// Amplifier's compliance posture (docs/PHASE_0_SPEC.md section 4 note,
// ARCHITECTURE_PLAN.md section 5).

import { createClient } from "jsr:@supabase/supabase-js@2";

const AMPLIFIER_API_BASE = "https://api.amplifierhealth.com";
const AMPLIFIER_ACCOUNT_ID = Deno.env.get("AMPLIFIER_ACCOUNT_ID")!;
const AMPLIFIER_API_KEY = Deno.env.get("AMPLIFIER_API_KEY")!;
const SUPABASE_URL = Deno.env.get("SUPABASE_URL")!;
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!;

function todayLocalDate(): string {
  return new Date().toISOString().slice(0, 10);
}

async function authenticate(req: Request) {
  const authHeader = req.headers.get("Authorization");
  if (!authHeader) return null;

  const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY);
  const token = authHeader.replace("Bearer ", "");
  const { data, error } = await supabase.auth.getUser(token);
  if (error || !data.user) return null;
  return { supabase, userId: data.user.id };
}

async function handleAnalyze(req: Request, sign: string): Promise<Response> {
  const auth = await authenticate(req);
  if (!auth) return new Response("unauthorized", { status: 401 });

  const incomingForm = await req.formData();
  const audio = incomingForm.get("audio");
  if (!(audio instanceof File)) {
    return new Response("missing audio part", { status: 400 });
  }

  const outgoingForm = new FormData();
  outgoingForm.append("audio", audio, audio.name);

  const lamResponse = await fetch(`${AMPLIFIER_API_BASE}/v2/signs/${sign}/analyze`, {
    method: "POST",
    headers: {
      "X-Account-ID": AMPLIFIER_ACCOUNT_ID,
      "X-API-Key": AMPLIFIER_API_KEY,
    },
    body: outgoingForm,
  });

  if (!lamResponse.ok) {
    return new Response(await lamResponse.text(), { status: lamResponse.status });
  }

  const lamJson = await lamResponse.json();
  const jobId = lamJson.job_id as string;

  await auth.supabase.from("daily_checks").upsert(
    {
      user_id: auth.userId,
      sign,
      local_date: todayLocalDate(),
      job_id: jobId,
      status: "processing",
    },
    { onConflict: "user_id,sign,local_date" },
  );

  return Response.json({ job_id: jobId });
}

async function handleJobStatus(req: Request, jobId: string): Promise<Response> {
  const auth = await authenticate(req);
  if (!auth) return new Response("unauthorized", { status: 401 });

  const lamResponse = await fetch(`${AMPLIFIER_API_BASE}/v2/jobs/${jobId}`, {
    headers: {
      "X-Account-ID": AMPLIFIER_ACCOUNT_ID,
      "X-API-Key": AMPLIFIER_API_KEY,
    },
  });

  if (!lamResponse.ok) {
    return new Response(await lamResponse.text(), { status: lamResponse.status });
  }

  const lamJson = await lamResponse.json();
  const status = lamJson.status as string; // pending/processing/done/failed
  const signal = lamJson.signal
    ? {
        level: lamJson.signal.level ?? null,
        score: lamJson.signal.score ?? null,
        flagged: lamJson.signal.flagged ?? false,
        // description / vocal_features intentionally dropped. Never
        // forwarded to the consumer client.
      }
    : null;
  const audioQualityIssue = lamJson.audio_quality_issue ?? null;

  if (status === "done" || status === "failed") {
    await auth.supabase
      .from("daily_checks")
      .update({
        status,
        level: signal?.level ?? null,
        score: signal?.score ?? null,
        flagged: signal?.flagged ?? false,
        audio_quality_issue: audioQualityIssue,
        error_reason: status === "failed" ? lamJson.error ?? "unknown" : null,
        completed_at: new Date().toISOString(),
      })
      .eq("user_id", auth.userId)
      .eq("job_id", jobId);
  }

  return Response.json({
    job_id: jobId,
    status,
    signal,
    audio_quality_issue: audioQualityIssue,
    error: lamJson.error ?? null,
  });
}

Deno.serve(async (req) => {
  const url = new URL(req.url);
  const segments = url.pathname.split("/").filter(Boolean);

  // Expect a path ending in signs/:sign/analyze or jobs/:jobId, with any
  // function-base prefix (e.g. /amplifier-proxy) before it.
  const signsIndex = segments.indexOf("signs");
  const jobsIndex = segments.indexOf("jobs");

  try {
    if (req.method === "POST" && signsIndex !== -1 && segments[signsIndex + 2] === "analyze") {
      return await handleAnalyze(req, segments[signsIndex + 1]);
    }
    if (req.method === "GET" && jobsIndex !== -1 && segments[jobsIndex + 1]) {
      return await handleJobStatus(req, segments[jobsIndex + 1]);
    }
    return new Response("not found", { status: 404 });
  } catch (err) {
    console.error(err);
    return new Response("internal error", { status: 500 });
  }
});
