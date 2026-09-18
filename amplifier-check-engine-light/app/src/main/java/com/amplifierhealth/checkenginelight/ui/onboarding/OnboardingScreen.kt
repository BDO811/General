package com.amplifierhealth.checkenginelight.ui.onboarding

import android.Manifest
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.amplifierhealth.checkenginelight.ui.ServiceLocator
import kotlinx.coroutines.launch

/**
 * ARCHITECTURE_PLAN.md section 5, Onboarding/consent: mic permission
 * rationale, plain-language data use disclosure, and "not a diagnostic
 * device" language, all shown before the first recording can happen.
 */
@Composable
fun OnboardingScreen(onContinue: () -> Unit) {
    val context = LocalContext.current
    val preferences = ServiceLocator.preferences(context)
    val scope = rememberCoroutineScope()

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        if (granted) {
            scope.launch {
                preferences.setOnboardingComplete(true)
                onContinue()
            }
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
    ) {
        Text("Amplifier Check", style = MaterialTheme.typography.headlineLarge)
        Spacer(Modifier.height(16.dp))
        Text(
            "Once a day, around noon, we'll ask for a 15-30 second voice sample. " +
                "Nothing to log, nothing to type. Just talk.",
            style = MaterialTheme.typography.bodyLarge,
        )
        Spacer(Modifier.height(16.dp))
        Text(
            "Your voice sample is analyzed by Amplifier's voice model to produce a daily " +
                "signal: green, yellow, or red. Recording only happens when you tap Record; " +
                "the app never listens in the background.",
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(Modifier.height(16.dp))
        Text(
            "This is not a diagnostic device. It does not detect, diagnose, or treat any " +
                "condition, and it is not a substitute for medical care.",
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(Modifier.height(32.dp))
        Button(onClick = {
            val alreadyGranted = ContextCompat.checkSelfPermission(
                context, Manifest.permission.RECORD_AUDIO,
            ) == PackageManager.PERMISSION_GRANTED

            if (alreadyGranted) {
                scope.launch {
                    preferences.setOnboardingComplete(true)
                    onContinue()
                }
            } else {
                permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }) {
            Text("Continue")
        }
    }
}
