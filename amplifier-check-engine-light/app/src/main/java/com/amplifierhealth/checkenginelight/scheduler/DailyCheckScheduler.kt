package com.amplifierhealth.checkenginelight.scheduler

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import java.time.Duration
import java.time.LocalDateTime
import java.time.ZoneId
import java.util.concurrent.TimeUnit
import kotlin.random.Random

/**
 * Owns both trigger paths from ARCHITECTURE_PLAN.md section 5 (Scheduler):
 * a WorkManager periodic job as the primary driver, and an exact alarm as a
 * Doze-resistant backup. Both target the 11:45am-12:15pm jitter window, not
 * a fixed clock time, per the same section.
 *
 * Both paths only ever post a reminder notification (via DailyCheckWorker);
 * neither one touches the microphone. Recording only happens from explicit
 * user action on the recording screen.
 */
class DailyCheckScheduler(private val context: Context) {

    fun scheduleDailyCheck() {
        schedulePeriodicWork()
        scheduleBackupAlarm()
    }

    fun rescheduleBackupAlarmForTomorrow() {
        scheduleBackupAlarm()
    }

    private fun schedulePeriodicWork() {
        val request = PeriodicWorkRequestBuilder<DailyCheckWorker>(
            1, TimeUnit.DAYS,
            FLEX_WINDOW_MINUTES, TimeUnit.MINUTES,
        )
            .setInitialDelay(minutesUntilNextWindowStart(), TimeUnit.MINUTES)
            .build()

        WorkManager.getInstance(context).enqueueUniquePeriodicWork(
            WORK_NAME,
            ExistingPeriodicWorkPolicy.KEEP,
            request,
        )
    }

    private fun scheduleBackupAlarm() {
        val alarmManager = context.getSystemService(AlarmManager::class.java) ?: return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && !alarmManager.canScheduleExactAlarms()) {
            // No exact-alarm permission granted; the periodic WorkManager job
            // (already flex-scheduled) is the sole trigger. Not a hard failure.
            return
        }

        val pendingIntent = PendingIntent.getBroadcast(
            context,
            BACKUP_ALARM_REQUEST_CODE,
            Intent(context, ExactAlarmReceiver::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        alarmManager.setExactAndAllowWhileIdle(
            AlarmManager.RTC_WAKEUP,
            nextJitteredNoonEpochMillis(),
            pendingIntent,
        )
    }

    private fun minutesUntilNextWindowStart(): Long {
        val now = LocalDateTime.now()
        var target = now.toLocalDate().atTime(WINDOW_START_HOUR, WINDOW_START_MINUTE)
        if (!target.isAfter(now)) target = target.plusDays(1)
        return Duration.between(now, target).toMinutes().coerceAtLeast(0)
    }

    private fun nextJitteredNoonEpochMillis(): Long {
        val jitterMinutes = Random.nextInt(-JITTER_HALF_WIDTH_MINUTES, JITTER_HALF_WIDTH_MINUTES + 1)
        val now = LocalDateTime.now()
        var target = now.toLocalDate().atTime(12, 0).plusMinutes(jitterMinutes.toLong())
        if (!target.isAfter(now)) target = target.plusDays(1)
        return target.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
    }

    companion object {
        const val WORK_NAME = "daily_check_reminder"
        private const val BACKUP_ALARM_REQUEST_CODE = 4200

        private const val WINDOW_START_HOUR = 11
        private const val WINDOW_START_MINUTE = 45
        private const val FLEX_WINDOW_MINUTES = 30L
        private const val JITTER_HALF_WIDTH_MINUTES = 15
    }
}
