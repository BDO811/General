package com.amplifierhealth.checkenginelight.audio

import okhttp3.MediaType
import okhttp3.RequestBody
import okio.BufferedSink
import okio.source

/**
 * Streams the decrypted bytes of an on-disk encrypted clip straight into the
 * upload body, so the app never materializes a second plaintext copy on disk
 * just to upload it. Content length is unknown up front (encryption framing
 * means ciphertext size isn't the plaintext size), so this uploads chunked.
 */
class DecryptingRequestBody(
    private val secureAudioStore: SecureAudioStore,
    private val ciphertextFile: java.io.File,
    private val mediaType: MediaType,
) : RequestBody() {

    override fun contentType(): MediaType = mediaType

    override fun contentLength(): Long = -1

    override fun writeTo(sink: BufferedSink) {
        secureAudioStore.openDecryptedStream(ciphertextFile).use { input ->
            sink.writeAll(input.source())
        }
    }
}
