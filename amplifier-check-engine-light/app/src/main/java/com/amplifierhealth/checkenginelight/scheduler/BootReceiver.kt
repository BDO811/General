package com.amplifierhealth.checkenginelight.scheduler

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent

/** Re-arms both the periodic job and the exact-alarm backup after a reboot. */
class BootReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            DailyCheckScheduler(context).scheduleDailyCheck()
        }
    }
}
