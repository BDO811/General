package com.amplifierhealth.checkenginelight.notification

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationCompat
import com.amplifierhealth.checkenginelight.MainActivity
import com.amplifierhealth.checkenginelight.R
import com.amplifierhealth.checkenginelight.model.SignalLevel

object AppNotifications {

    const val CHANNEL_REMINDER = "daily_reminder"
    const val CHANNEL_RECORDING = "recording_in_progress"
    const val CHANNEL_RESULT = "daily_result"

    const val ID_RECORDING_SERVICE = 1001
    const val ID_RESULT = 1002

    fun registerChannels(context: Context) {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val manager = context.getSystemService(NotificationManager::class.java)

        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_REMINDER,
                context.getString(R.string.channel_reminder_name),
                NotificationManager.IMPORTANCE_DEFAULT,
            ).apply { description = context.getString(R.string.channel_reminder_desc) }
        )

        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_RECORDING,
                context.getString(R.string.channel_recording_name),
                NotificationManager.IMPORTANCE_LOW,
            ).apply { description = context.getString(R.string.channel_recording_desc) }
        )

        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_RESULT,
                context.getString(R.string.channel_result_name),
                NotificationManager.IMPORTANCE_DEFAULT,
            ).apply { description = context.getString(R.string.channel_result_desc) }
        )
    }

    /** The once-a-day prompt that fires inside the jittered noon window. */
    fun buildReminderNotification(context: Context): android.app.Notification {
        val openIntent = Intent(context, MainActivity::class.java).apply {
            putExtra(MainActivity.EXTRA_LAUNCH_RECORDING, true)
        }
        val pendingIntent = PendingIntent.getActivity(
            context, 0, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        return NotificationCompat.Builder(context, CHANNEL_REMINDER)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(context.getString(R.string.reminder_notification_title))
            .setContentText(context.getString(R.string.reminder_notification_body))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
    }

    /** Foreground-service notification, visible only while the mic is actually open. */
    fun buildRecordingServiceNotification(context: Context): android.app.Notification {
        return NotificationCompat.Builder(context, CHANNEL_RECORDING)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(context.getString(R.string.recording_notification_title))
            .setContentText(context.getString(R.string.recording_notification_body))
            .setOngoing(true)
            .build()
    }

    fun showResultNotification(context: Context, level: SignalLevel) {
        val manager = context.getSystemService(NotificationManager::class.java)
        val bodyRes = when (level) {
            SignalLevel.GREEN -> R.string.result_notification_body_green
            SignalLevel.YELLOW -> R.string.result_notification_body_yellow
            SignalLevel.RED -> R.string.result_notification_body_red
            SignalLevel.GRAY -> R.string.result_notification_body_gray
        }
        val openIntent = Intent(context, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            context, 0, openIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE,
        )
        val notification = NotificationCompat.Builder(context, CHANNEL_RESULT)
            .setSmallIcon(R.drawable.ic_notification)
            .setContentTitle(context.getString(R.string.result_notification_title))
            .setContentText(context.getString(bodyRes))
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()
        manager.notify(ID_RESULT, notification)
    }
}
