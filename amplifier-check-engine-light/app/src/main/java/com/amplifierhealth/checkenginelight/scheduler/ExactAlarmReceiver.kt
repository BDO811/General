package com.amplifierhealth.checkenginelight.scheduler

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager

/**
 * Backup trigger for devices where the periodic WorkManager job gets
 * deferred by Doze/App Standby past the jitter window. Runs the same
 * DailyCheckWorker logic (which is itself idempotent against a day that's
 * already recorded), then re-arms itself for tomorrow.
 */
class ExactAlarmReceiver : BroadcastReceiver() {

    override fun onReceive(context: Context, intent: Intent) {
        WorkManager.getInstance(context).enqueue(OneTimeWorkRequestBuilder<DailyCheckWorker>().build())
        DailyCheckScheduler(context).rescheduleBackupAlarmForTomorrow()
    }
}
