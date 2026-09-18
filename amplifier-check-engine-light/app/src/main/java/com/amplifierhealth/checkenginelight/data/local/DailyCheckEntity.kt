package com.amplifierhealth.checkenginelight.data.local

import androidx.room.Entity
import androidx.room.PrimaryKey
import java.time.LocalDate

/**
 * Local mirror of the `daily_checks` row for this device (see
 * docs/PHASE_0_SPEC.md section 4 for the Supabase schema this tracks).
 * Only ever holds level/score/status, never the LAM `description` or
 * `vocal_features` narrative fields, which are care-staff-only.
 */
@Entity(tableName = "daily_checks")
data class DailyCheckEntity(
    @PrimaryKey val localDate: LocalDate,
    val sign: String = "dehydration",
    val jobId: String? = null,
    val level: String? = null,
    val score: Double? = null,
    val flagged: Boolean = false,
    val audioQualityIssue: String? = null,
    val status: CheckStatus = CheckStatus.PENDING,
    val requestedAtEpochMillis: Long,
    val completedAtEpochMillis: Long? = null,
    val errorReason: String? = null,
)

enum class CheckStatus {
    PENDING,
    UPLOADING,
    PROCESSING,
    DONE,
    FAILED,
}
