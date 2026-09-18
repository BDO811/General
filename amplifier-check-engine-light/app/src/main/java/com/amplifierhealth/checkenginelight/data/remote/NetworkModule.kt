package com.amplifierhealth.checkenginelight.data.remote

import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import java.util.concurrent.TimeUnit

/**
 * Points at the Supabase edge function proxy fronting the Amplifier LAM API
 * (ARCHITECTURE_PLAN.md section 3). Swap for the real project ref before
 * shipping Phase 1; this is intentionally not hardcoded to a production
 * value in source control.
 */
object NetworkModule {

    const val PROXY_BASE_URL = "https://YOUR-SUPABASE-PROJECT.functions.supabase.co/amplifier-proxy/"

    fun buildOkHttpClient(debugLogging: Boolean): OkHttpClient {
        val builder = OkHttpClient.Builder()
            .connectTimeout(15, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)

        if (debugLogging) {
            builder.addInterceptor(HttpLoggingInterceptor().apply { level = HttpLoggingInterceptor.Level.BASIC })
        }
        return builder.build()
    }

    fun buildApi(debugLogging: Boolean = false): AmplifierProxyApi =
        AmplifierProxyApi.create(PROXY_BASE_URL, buildOkHttpClient(debugLogging))
}

/**
 * Supplies the Supabase session token the proxy uses to authenticate the
 * caller (the proxy itself holds the Amplifier account credentials; see
 * ARCHITECTURE_PLAN.md section 3). Real Phase 1 wiring needs a decision on
 * the auth flow (e.g. Supabase anonymous auth vs. a lightweight sign-in);
 * that decision isn't made by this architecture plan and is an open item
 * for whoever wires up account creation, not something to guess here.
 */
interface AuthTokenProvider {
    suspend fun bearerToken(): String
}
