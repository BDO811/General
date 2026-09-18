package com.amplifierhealth.checkenginelight.ui.settings

import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.getSystemService
import com.amplifierhealth.checkenginelight.ui.ServiceLocator
import kotlinx.coroutines.launch

/**
 * ARCHITECTURE_PLAN.md section 5 (UI, Reliability). Re-shows the "not a
 * diagnostic device" disclosure (not just at onboarding) and prompts for
 * the battery-optimization exemption. Doze mode is the single most common
 * reason the scheduled noon check silently stops firing.
 */
@Composable
fun SettingsScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val preferences = remember { ServiceLocator.preferences(context) }
    val scope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().padding(24.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("Settings", style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = onBack) { Text("Back") }
        }

        Spacer(Modifier.height(24.dp))
        Text(
            "This app is not a diagnostic device. It does not detect, diagnose, or treat " +
                "any condition, and it is not a substitute for medical care.",
            style = MaterialTheme.typography.bodyMedium,
        )

        Spacer(Modifier.height(32.dp))
        Text("Reliability", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(8.dp))
        Text(
            "If your phone's battery saver is aggressive, the daily reminder can get " +
                "delayed or skipped. Exempting this app fixes that.",
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(Modifier.height(12.dp))
        Button(onClick = {
            requestBatteryOptimizationExemption(context)
            scope.launch { preferences.setBatteryOptPromptShown(true) }
        }) {
            Text(if (isIgnoringBatteryOptimizations(context)) "Battery exemption granted" else "Exempt from battery optimization")
        }
    }
}

private fun isIgnoringBatteryOptimizations(context: android.content.Context): Boolean {
    val powerManager = context.getSystemService<PowerManager>() ?: return false
    return powerManager.isIgnoringBatteryOptimizations(context.packageName)
}

private fun requestBatteryOptimizationExemption(context: android.content.Context) {
    if (Build.VERSION.SDK_INT < Build.VERSION_CODES.M) return
    if (isIgnoringBatteryOptimizations(context)) return
    val intent = Intent(
        Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
        Uri.parse("package:${context.packageName}"),
    )
    context.startActivity(intent)
}
