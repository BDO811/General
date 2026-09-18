package com.amplifierhealth.checkenginelight.capture

import android.app.Service
import android.content.Intent
import android.os.Build
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import androidx.work.Data
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.amplifierhealth.checkenginelight.audio.AudioRecorder
import com.amplifierhealth.checkenginelight.audio.SecureAudioStore
import com.amplifierhealth.checkenginelight.notification.AppNotifications
import com.amplifierhealth.checkenginelight.scheduler.UploadWorker

/**
 * Foreground service that owns the mic for exactly one 15-30s clip
 * (ARCHITECTURE_PLAN.md section 5, Capture). Started only by direct user
 * action from the recording screen; it is never scheduled to start itself.
 * On stop, it encrypts the clip, deletes the plaintext, and hands off to
 * UploadWorker; the service itself never talks to the network.
 */
class RecordingForegroundService : Service() {

    private val audioRecorder = AudioRecorder()
    private lateinit var secureAudioStore: SecureAudioStore
    private var plaintextFile: java.io.File? = null
    private val handler = Handler(Looper.getMainLooper())

    override fun onCreate() {
        super.onCreate()
        secureAudioStore = SecureAudioStore(applicationContext)
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopRecordingAndUpload()
            return START_NOT_STICKY
        }

        startForeground(AppNotifications.ID_RECORDING_SERVICE, AppNotifications.buildRecordingServiceNotification(this))

        val file = secureAudioStore.newPlaintextScratchFile()
        plaintextFile = file
        audioRecorder.start(file)

        // Auto-stop at the max clip duration even if the UI never sends ACTION_STOP,
        // so the foreground service can't be left running indefinitely.
        handler.postDelayed({ stopRecordingAndUpload() }, AudioRecorder.MAX_DURATION_MS.toLong())

        return START_NOT_STICKY
    }

    fun stopRecordingAndUpload() {
        handler.removeCallbacksAndMessages(null)
        audioRecorder.stop()

        val plaintext = plaintextFile
        if (plaintext != null && plaintext.exists()) {
            val ciphertextFile = secureAudioStore.encryptAndDiscardPlaintext(plaintext)
            enqueueUpload(ciphertextFile.absolutePath)
        }
        stopSelf()
    }

    private fun enqueueUpload(ciphertextPath: String) {
        val request = OneTimeWorkRequestBuilder<UploadWorker>()
            .setInputData(Data.Builder().putString(UploadWorker.KEY_CIPHERTEXT_PATH, ciphertextPath).build())
            .build()
        WorkManager.getInstance(applicationContext).enqueue(request)
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        handler.removeCallbacksAndMessages(null)
        super.onDestroy()
    }

    companion object {
        const val ACTION_STOP = "com.amplifierhealth.checkenginelight.capture.ACTION_STOP"
    }
}
