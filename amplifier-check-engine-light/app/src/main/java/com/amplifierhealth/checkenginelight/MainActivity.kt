package com.amplifierhealth.checkenginelight

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.amplifierhealth.checkenginelight.ui.navigation.AppNavHost
import com.amplifierhealth.checkenginelight.ui.theme.CheckEngineLightTheme

class MainActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()

        val startWithRecording = intent?.getBooleanExtra(EXTRA_LAUNCH_RECORDING, false) ?: false

        setContent {
            CheckEngineLightTheme {
                Surface(modifier = Modifier.fillMaxSize()) {
                    AppNavHost(startWithRecording = startWithRecording)
                }
            }
        }
    }

    companion object {
        const val EXTRA_LAUNCH_RECORDING = "launch_recording"
    }
}
