package com.amplifierhealth.checkenginelight

import android.app.Application
import com.amplifierhealth.checkenginelight.notification.AppNotifications
import com.amplifierhealth.checkenginelight.scheduler.DailyCheckScheduler

class CheckEngineApp : Application() {

    override fun onCreate() {
        super.onCreate()
        AppNotifications.registerChannels(this)
        // Idempotent: re-arms the periodic work + backup alarm on every process
        // start (app open, boot, or after being killed by the system), rather
        // than relying on a single scheduling call surviving forever.
        DailyCheckScheduler(this).scheduleDailyCheck()
    }
}
