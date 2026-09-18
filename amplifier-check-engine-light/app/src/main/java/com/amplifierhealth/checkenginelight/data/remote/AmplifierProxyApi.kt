package com.amplifierhealth.checkenginelight.data.remote

import com.amplifierhealth.checkenginelight.data.remote.dto.AnalyzeJobResponse
import com.amplifierhealth.checkenginelight.data.remote.dto.JobStatusResponse
import okhttp3.MultipartBody
import retrofit2.Retrofit
import retrofit2.converter.moshi.MoshiConverterFactory
import retrofit2.http.GET
import retrofit2.http.Header
import retrofit2.http.Multipart
import retrofit2.http.POST
import retrofit2.http.Part
import retrofit2.http.Path

/**
 * Talks only to the Supabase edge function proxy, never directly to
 * api.amplifierhealth.com. The proxy is the only thing holding
 * X-Account-ID / X-API-Key (see ARCHITECTURE_PLAN.md section 3 and
 * supabase/functions/amplifier-proxy). The client authenticates to the
 * proxy with the user's own Supabase session token.
 */
interface AmplifierProxyApi {

    @Multipart
    @POST("signs/{sign}/analyze")
    suspend fun submitClip(
        @Path("sign") sign: String,
        @Part audio: MultipartBody.Part,
        @Header("Authorization") bearerToken: String,
    ): AnalyzeJobResponse

    @GET("jobs/{jobId}")
    suspend fun getJobStatus(
        @Path("jobId") jobId: String,
        @Header("Authorization") bearerToken: String,
    ): JobStatusResponse

    companion object {
        fun create(baseUrl: String, okHttpClient: okhttp3.OkHttpClient): AmplifierProxyApi {
            return Retrofit.Builder()
                .baseUrl(baseUrl)
                .client(okHttpClient)
                .addConverterFactory(MoshiConverterFactory.create())
                .build()
                .create(AmplifierProxyApi::class.java)
        }
    }
}
