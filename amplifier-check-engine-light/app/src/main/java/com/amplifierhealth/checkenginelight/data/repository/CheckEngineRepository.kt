package com.amplifierhealth.checkenginelight.data.repository

import com.amplifierhealth.checkenginelight.audio.DecryptingRequestBody
import com.amplifierhealth.checkenginelight.audio.SecureAudioStore
import com.amplifierhealth.checkenginelight.data.local.CheckStatus
import com.amplifierhealth.checkenginelight.data.local.DailyCheckDao
import com.amplifierhealth.checkenginelight.data.local.DailyCheckEntity
import com.amplifierhealth.checkenginelight.data.remote.AmplifierProxyApi
import kotlinx.coroutines.flow.Flow
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import java.io.File
import java.time.LocalDate

private const val SIGN = "dehydration" // locked in docs/PHASE_0_SPEC.md section 2

class CheckEngineRepository(
    private val dao: DailyCheckDao,
    private val api: AmplifierProxyApi,
    private val secureAudioStore: SecureAudioStore,
    private val bearerTokenProvider: suspend () -> String,
) {

    fun observeLatest(): Flow<DailyCheckEntity?> = dao.observeLatest()

    fun observeHistory(limit: Int = 90): Flow<List<DailyCheckEntity>> = dao.observeHistory(limit)

    suspend fun todaysCheck(today: LocalDate = LocalDate.now()): DailyCheckEntity? =
        dao.getForDate(today)

    /** Marks today's row as recorded and queued for upload. */
    suspend fun markRecorded(today: LocalDate = LocalDate.now()) {
        dao.upsert(
            DailyCheckEntity(
                localDate = today,
                sign = SIGN,
                status = CheckStatus.UPLOADING,
                requestedAtEpochMillis = System.currentTimeMillis(),
            )
        )
    }

    /**
     * Uploads the encrypted clip [ciphertextFile] (as produced by
     * SecureAudioStore.encryptAndDiscardPlaintext) and returns the job id.
     * Caller (UploadWorker) polls separately.
     */
    suspend fun submitClip(ciphertextFile: File, today: LocalDate = LocalDate.now()): String {
        val requestBody = DecryptingRequestBody(secureAudioStore, ciphertextFile, "audio/mp4".toMediaType())
        val part = MultipartBody.Part.createFormData("audio", "clip.m4a", requestBody)
        val response = api.submitClip(SIGN, part, bearerTokenProvider())

        dao.upsert(
            (dao.getForDate(today) ?: DailyCheckEntity(
                localDate = today,
                requestedAtEpochMillis = System.currentTimeMillis(),
            )).copy(
                sign = SIGN,
                jobId = response.jobId,
                status = CheckStatus.PROCESSING,
            )
        )
        return response.jobId
    }

    suspend fun pollJob(jobId: String, today: LocalDate = LocalDate.now()) {
        val status = api.getJobStatus(jobId, bearerTokenProvider())
        val existing = dao.getForDate(today) ?: DailyCheckEntity(
            localDate = today,
            jobId = jobId,
            requestedAtEpochMillis = System.currentTimeMillis(),
        )

        when (status.status) {
            "done" -> dao.upsert(
                existing.copy(
                    level = status.signal?.level,
                    score = status.signal?.score,
                    flagged = status.signal?.flagged ?: false,
                    audioQualityIssue = status.audioQualityIssue,
                    status = CheckStatus.DONE,
                    completedAtEpochMillis = System.currentTimeMillis(),
                )
            )
            "failed" -> dao.upsert(
                existing.copy(status = CheckStatus.FAILED, errorReason = status.error)
            )
            else -> dao.upsert(existing.copy(status = CheckStatus.PROCESSING))
        }
    }

    suspend fun markFailed(reason: String, today: LocalDate = LocalDate.now()) {
        val existing = dao.getForDate(today) ?: DailyCheckEntity(
            localDate = today,
            requestedAtEpochMillis = System.currentTimeMillis(),
        )
        dao.upsert(existing.copy(status = CheckStatus.FAILED, errorReason = reason))
    }
}
