package com.amplifierhealth.checkenginelight.scheduler

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.amplifierhealth.checkenginelight.data.local.AppDatabase
import com.amplifierhealth.checkenginelight.notification.AppNotifications
import java.time.LocalDate

/**
 * The primary noon trigger (ARCHITECTURE_PLAN.md section 5, Scheduler).
 * WorkManager itself provides the jitter: it's enqueued as periodic work
 * with a daily flex window rather than an exact time, which is also what
 * keeps this off Play's "exact background alarm" scrutiny for the common
 * case. ExactAlarmReceiver is the backup path for devices where WorkManager
 * gets deferred too far past noon.
 *
 * This worker never touches the microphone itself. It only posts the
 * reminder notification that opens the recording screen. All capture is
 * user-initiated from there.
 */
class DailyCheckWorker(context: Context, params: WorkerParameters) : CoroutineWorker(context, params) {

    override suspend fun doWork(): Result {
        val today = LocalDate.now()
        val dao = AppDatabase.get(applicationContext).dailyCheckDao()
        val existing = dao.getForDate(today)

        // Already recorded (or already retried and failed) today; don't nag again.
        if (existing != null) return Result.success()

        val notification = AppNotifications.buildReminderNotification(applicationContext)
        val manager = applicationContext.getSystemService(android.app.NotificationManager::class.java)
        manager.notify(AppNotifications.ID_RESULT + 1, notification)

        return Result.success()
    }
}
