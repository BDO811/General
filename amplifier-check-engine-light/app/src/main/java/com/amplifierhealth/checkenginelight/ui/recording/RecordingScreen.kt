package com.amplifierhealth.checkenginelight.ui.recording

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.amplifierhealth.checkenginelight.audio.AudioRecorder
import com.amplifierhealth.checkenginelight.capture.RecordingForegroundService
import kotlinx.coroutines.delay

private enum class RecordingPhase { REQUESTING_PERMISSION, READY, RECORDING, DONE }

/**
 * Manual, user-initiated 15-30s capture (ARCHITECTURE_PLAN.md section 5,
 * Capture). Starts RecordingForegroundService, which owns the mic; this
 * screen only drives the countdown UI and the stop signal.
 */
@Composable
fun RecordingScreen(onDone: () -> Unit) {
    val context = LocalContext.current
    var secondsRemaining by remember { mutableIntStateOf(AudioRecorder.MAX_DURATION_MS / 1000) }
    var currentPhase by remember { mutableStateOf(RecordingPhase.REQUESTING_PERMISSION) }

    val permissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        currentPhase = if (granted) RecordingPhase.READY else RecordingPhase.DONE
    }

    LaunchedEffect(Unit) {
        val granted = ContextCompat.checkSelfPermission(
            context, Manifest.permission.RECORD_AUDIO,
        ) == PackageManager.PERMISSION_GRANTED
        currentPhase = if (granted) RecordingPhase.READY else RecordingPhase.REQUESTING_PERMISSION
        if (!granted) permissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
    }

    LaunchedEffect(currentPhase) {
        if (currentPhase == RecordingPhase.RECORDING) {
            secondsRemaining = AudioRecorder.MAX_DURATION_MS / 1000
            while (secondsRemaining > 0) {
                delay(1000)
                secondsRemaining -= 1
            }
            currentPhase = RecordingPhase.DONE
            onDone()
        }
    }

    Column(
        modifier = Modifier.fillMaxSize().padding(24.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally,
    ) {
        when (currentPhase) {
            RecordingPhase.REQUESTING_PERMISSION -> Text("Waiting for microphone permission")
            RecordingPhase.READY -> {
                Text("Talk about your day for 15-30 seconds.", style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.height(24.dp))
                Button(onClick = {
                    ContextCompat.startForegroundService(
                        context, Intent(context, RecordingForegroundService::class.java),
                    )
                    currentPhase = RecordingPhase.RECORDING
                }) {
                    Text("Start")
                }
            }
            RecordingPhase.RECORDING -> {
                Text("Recording", style = MaterialTheme.typography.headlineMedium)
                Spacer(Modifier.height(16.dp))
                Text("$secondsRemaining s left", style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.height(24.dp))
                Button(onClick = {
                    context.startService(
                        Intent(context, RecordingForegroundService::class.java)
                            .setAction(RecordingForegroundService.ACTION_STOP),
                    )
                    currentPhase = RecordingPhase.DONE
                    onDone()
                }) {
                    Text("Stop early")
                }
            }
            RecordingPhase.DONE -> Text("Thanks. We're processing today's check.")
        }
    }
}
