package com.amplifierhealth.checkenginelight.ui

import android.content.Context
import com.amplifierhealth.checkenginelight.audio.SecureAudioStore
import com.amplifierhealth.checkenginelight.data.local.AppDatabase
import com.amplifierhealth.checkenginelight.data.prefs.UserPreferences
import com.amplifierhealth.checkenginelight.data.remote.NetworkModule
import com.amplifierhealth.checkenginelight.data.repository.CheckEngineRepository

/**
 * Minimal manual wiring for a Phase 1 scaffold. A Hilt/Koin graph is easy
 * to add later but isn't warranted at this scope. UI code only ever reads
 * local Flow state from the repository; network calls belong to UploadWorker.
 */
object ServiceLocator {

    @Volatile private var repository: CheckEngineRepository? = null

    fun repository(context: Context): CheckEngineRepository = repository ?: synchronized(this) {
        repository ?: CheckEngineRepository(
            dao = AppDatabase.get(context).dailyCheckDao(),
            api = NetworkModule.buildApi(debugLogging = false),
            secureAudioStore = SecureAudioStore(context),
            bearerTokenProvider = {
                throw NotImplementedError("AuthTokenProvider not wired yet. See NetworkModule.kt TODO(auth).")
            },
        ).also { repository = it }
    }

    fun preferences(context: Context): UserPreferences = UserPreferences(context)
}
