package com.amplifierhealth.checkenginelight.audio

import android.content.Context
import androidx.security.crypto.EncryptedFile
import androidx.security.crypto.MasterKey
import java.io.File
import java.io.InputStream

/**
 * Manages the raw clip during the brief window between recording and a
 * successful/failed upload (ARCHITECTURE_PLAN.md section 5, Local storage).
 *
 * MediaRecorder can't write its muxed output directly into an EncryptedFile
 * stream, so capture writes a plaintext scratch file first; this class then
 * encrypts it and deletes the plaintext immediately, so the plaintext only
 * exists on disk for the recording's own duration, never across the upload.
 * The ciphertext is deleted on a successful LAM response, or on failure once
 * the retry window closes. Never kept as long-term history; only derived
 * scores/levels persist (see DailyCheckEntity).
 */
class SecureAudioStore(private val context: Context) {

    private val masterKey by lazy {
        MasterKey.Builder(context).setKeyScheme(MasterKey.KeyScheme.AES256_GCM).build()
    }

    private val scratchDir: File by lazy {
        File(context.cacheDir, "recording_scratch").apply { mkdirs() }
    }

    private val pendingDir: File by lazy {
        File(context.filesDir, "pending_clips").apply { mkdirs() }
    }

    fun newPlaintextScratchFile(): File =
        File(scratchDir, "clip_${System.currentTimeMillis()}.m4a")

    /** Encrypts [plaintextFile] into a new ciphertext file, then deletes the plaintext. */
    fun encryptAndDiscardPlaintext(plaintextFile: File): File {
        val ciphertextFile = File(pendingDir, "${plaintextFile.name}.enc")
        val encryptedFile = openEncryptedFile(ciphertextFile)
        plaintextFile.inputStream().use { input ->
            encryptedFile.openFileOutput().use { output -> input.copyTo(output) }
        }
        plaintextFile.delete()
        return ciphertextFile
    }

    fun openDecryptedStream(ciphertextFile: File): InputStream =
        openEncryptedFile(ciphertextFile).openFileInput()

    private fun openEncryptedFile(ciphertextFile: File): EncryptedFile =
        EncryptedFile.Builder(
            context,
            ciphertextFile,
            masterKey,
            EncryptedFile.FileEncryptionScheme.AES256_GCM_HKDF_4KB,
        ).build()

    fun deleteAllPending() {
        pendingDir.listFiles()?.forEach { it.delete() }
        scratchDir.listFiles()?.forEach { it.delete() }
    }

    fun delete(file: File) {
        file.delete()
    }
}
