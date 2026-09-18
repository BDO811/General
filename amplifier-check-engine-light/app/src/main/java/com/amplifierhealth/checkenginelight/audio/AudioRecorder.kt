package com.amplifierhealth.checkenginelight.audio

import android.media.MediaRecorder
import java.io.File

/**
 * Thin wrapper over MediaRecorder producing a mono 16kHz clip, matching
 * LAM's recommended capture format (ARCHITECTURE_PLAN.md section 5, Capture).
 * Records at most [MAX_DURATION_MS] and always writes to a file the caller
 * already created inside the encrypted temp directory.
 */
class AudioRecorder {

    private var recorder: MediaRecorder? = null

    fun start(outputFile: File) {
        val mediaRecorder = MediaRecorder().apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.MPEG_4)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setAudioChannels(1)
            setAudioSamplingRate(SAMPLE_RATE_HZ)
            setOutputFile(outputFile.absolutePath)
            setMaxDuration(MAX_DURATION_MS)
            prepare()
            start()
        }
        recorder = mediaRecorder
    }

    fun stop() {
        recorder?.apply {
            try {
                stop()
            } finally {
                release()
            }
        }
        recorder = null
    }

    companion object {
        const val SAMPLE_RATE_HZ = 16_000
        const val MIN_DURATION_MS = 15_000
        const val MAX_DURATION_MS = 30_000
    }
}
