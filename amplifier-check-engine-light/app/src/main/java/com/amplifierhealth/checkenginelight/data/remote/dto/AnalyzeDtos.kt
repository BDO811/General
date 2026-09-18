package com.amplifierhealth.checkenginelight.data.remote.dto

import com.squareup.moshi.Json
import com.squareup.moshi.JsonClass

/**
 * Response from the Supabase proxy's `analyze` passthrough
 * (`POST /v2/signs/{sign}/analyze` on the Amplifier LAM API, per
 * ARCHITECTURE_PLAN.md section 3). The proxy holds the account credentials;
 * the client only ever sees a job id to poll.
 */
@JsonClass(generateAdapter = true)
data class AnalyzeJobResponse(
    @Json(name = "job_id") val jobId: String,
)

@JsonClass(generateAdapter = true)
data class JobStatusResponse(
    @Json(name = "job_id") val jobId: String,
    @Json(name = "status") val status: String, // pending/processing/done/failed
    @Json(name = "signal") val signal: SignalDto?,
    @Json(name = "audio_quality_issue") val audioQualityIssue: String?,
    @Json(name = "error") val error: String?,
)

@JsonClass(generateAdapter = true)
data class SignalDto(
    @Json(name = "level") val level: String?,
    @Json(name = "score") val score: Double?,
    @Json(name = "flagged") val flagged: Boolean = false,
    // Deliberately no `description` / `vocal_features` field here: those are
    // care-staff-only per Amplifier's compliance posture and must never be
    // parsed into a model the consumer client can render. See
    // ARCHITECTURE_PLAN.md section 5, Result handling.
)
