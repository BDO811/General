package com.amplifierhealth.checkenginelight.scheduler

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.amplifierhealth.checkenginelight.audio.SecureAudioStore
import com.amplifierhealth.checkenginelight.data.local.AppDatabase
import com.amplifierhealth.checkenginelight.data.local.CheckStatus
import com.amplifierhealth.checkenginelight.data.remote.NetworkModule
import com.amplifierhealth.checkenginelight.data.repository.CheckEngineRepository
import com.amplifierhealth.checkenginelight.model.SignalLevel
import com.amplifierhealth.checkenginelight.notification.AppNotifications
import kotlinx.coroutines.delay
import java.io.File
import java.time.LocalDate

/**
 * Implements the upload -> poll -> store -> cleanup -> notify pipeline from
 * the ARCHITECTURE_PLAN.md section 3 diagram. Runs the poll loop client-side
 * within one WorkManager execution; if the job isn't done within
 * [MAX_POLL_ATTEMPTS], the worker returns retry() so WorkManager re-runs it
 * later rather than blocking indefinitely (WorkManager execution windows are
 * bounded). A resumed run skips re-submitting the clip if a job id is
 * already recorded for today.
 */
class UploadWorker(
    private val context: Context,
    params: WorkerParameters,
) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val ciphertextPath = inputData.getString(KEY_CIPHERTEXT_PATH)
            ?: return Result.failure()
        val ciphertextFile = File(ciphertextPath)
        val today = LocalDate.now()

        val secureAudioStore = SecureAudioStore(context)
        val dao = AppDatabase.get(context).dailyCheckDao()
        val api = NetworkModule.buildApi(debugLogging = false)
        // TODO(auth): wire a real AuthTokenProvider once the Supabase auth
        // flow for this app is decided (see NetworkModule.AuthTokenProvider).
        val repository = CheckEngineRepository(dao, api, secureAudioStore) {
            throw NotImplementedError(
                "AuthTokenProvider not wired yet. See NetworkModule.kt TODO(auth)."
            )
        }

        return try {
            val existing = repository.todaysCheck(today)
            val jobId = if (existing?.jobId != null && existing.status == CheckStatus.PROCESSING) {
                existing.jobId
            } else {
                repository.submitClip(ciphertextFile, today)
            }

            val done = pollUntilDone(repository, jobId, today)
            if (!done) return Result.retry()

            val finalEntity = repository.todaysCheck(today)
            secureAudioStore.delete(ciphertextFile)

            val level = SignalLevel.fromApi(finalEntity?.level, finalEntity?.audioQualityIssue)
            AppNotifications.showResultNotification(context, level)
            Result.success()
        } catch (t: Throwable) {
            if (runAttemptCount >= MAX_WORKER_RETRIES) {
                repository.markFailed(t.message ?: "upload_failed", today)
                secureAudioStore.delete(ciphertextFile)
                Result.failure()
            } else {
                Result.retry()
            }
        }
    }

    private suspend fun pollUntilDone(
        repository: CheckEngineRepository,
        jobId: String,
        today: LocalDate,
    ): Boolean {
        repeat(MAX_POLL_ATTEMPTS) {
            repository.pollJob(jobId, today)
            val entity = repository.todaysCheck(today)
            if (entity?.status == CheckStatus.DONE || entity?.status == CheckStatus.FAILED) return true
            delay(POLL_INTERVAL_MS)
        }
        return false
    }

    companion object {
        const val KEY_CIPHERTEXT_PATH = "ciphertext_path"
        private const val POLL_INTERVAL_MS = 3_000L
        private const val MAX_POLL_ATTEMPTS = 20 // ~1 minute within this run
        private const val MAX_WORKER_RETRIES = 5
    }
}
