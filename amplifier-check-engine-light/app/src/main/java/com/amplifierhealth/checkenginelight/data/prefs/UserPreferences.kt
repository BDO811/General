package com.amplifierhealth.checkenginelight.data.prefs

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore(name = "check_engine_light_prefs")

/**
 * Small settings that don't warrant a DB table: onboarding/consent state,
 * the noon jitter window (minutes from midnight), and whether we've already
 * asked the user to exempt the app from battery optimization (plan section 5,
 * Reliability). Doze is the most common reason a scheduled task silently
 * stops firing, so we only want to ask once, not nag.
 */
class UserPreferences(private val context: Context) {

    private object Keys {
        val ONBOARDING_COMPLETE = booleanPreferencesKey("onboarding_complete")
        val BATTERY_OPT_PROMPT_SHOWN = booleanPreferencesKey("battery_opt_prompt_shown")
        val WINDOW_START_MINUTE = intPreferencesKey("window_start_minute")
        val WINDOW_END_MINUTE = intPreferencesKey("window_end_minute")
        val ACCOUNT_ID = stringPreferencesKey("account_id")
    }

    // 11:45am to 12:15pm, matching the jitter window in ARCHITECTURE_PLAN.md section 5.
    private val defaultWindowStartMinute = 11 * 60 + 45
    private val defaultWindowEndMinute = 12 * 60 + 15

    val onboardingComplete: Flow<Boolean> =
        context.dataStore.data.map { it[Keys.ONBOARDING_COMPLETE] ?: false }

    val batteryOptPromptShown: Flow<Boolean> =
        context.dataStore.data.map { it[Keys.BATTERY_OPT_PROMPT_SHOWN] ?: false }

    val windowStartMinute: Flow<Int> =
        context.dataStore.data.map { it[Keys.WINDOW_START_MINUTE] ?: defaultWindowStartMinute }

    val windowEndMinute: Flow<Int> =
        context.dataStore.data.map { it[Keys.WINDOW_END_MINUTE] ?: defaultWindowEndMinute }

    val accountId: Flow<String?> =
        context.dataStore.data.map { it[Keys.ACCOUNT_ID] }

    suspend fun setOnboardingComplete(complete: Boolean) {
        context.dataStore.edit { it[Keys.ONBOARDING_COMPLETE] = complete }
    }

    suspend fun setBatteryOptPromptShown(shown: Boolean) {
        context.dataStore.edit { it[Keys.BATTERY_OPT_PROMPT_SHOWN] = shown }
    }

    suspend fun setCheckWindow(startMinute: Int, endMinute: Int) {
        context.dataStore.edit {
            it[Keys.WINDOW_START_MINUTE] = startMinute
            it[Keys.WINDOW_END_MINUTE] = endMinute
        }
    }

    suspend fun setAccountId(accountId: String) {
        context.dataStore.edit { it[Keys.ACCOUNT_ID] = accountId }
    }
}
