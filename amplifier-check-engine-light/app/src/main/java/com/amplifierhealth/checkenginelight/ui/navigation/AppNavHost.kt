package com.amplifierhealth.checkenginelight.ui.navigation

import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.platform.LocalContext
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.amplifierhealth.checkenginelight.ui.ServiceLocator
import com.amplifierhealth.checkenginelight.ui.history.HistoryScreen
import com.amplifierhealth.checkenginelight.ui.home.HomeScreen
import com.amplifierhealth.checkenginelight.ui.onboarding.OnboardingScreen
import com.amplifierhealth.checkenginelight.ui.recording.RecordingScreen
import com.amplifierhealth.checkenginelight.ui.settings.SettingsScreen

object Destinations {
    const val ONBOARDING = "onboarding"
    const val HOME = "home"
    const val HISTORY = "history"
    const val SETTINGS = "settings"
    const val RECORDING = "recording"
}

@Composable
fun AppNavHost(startWithRecording: Boolean, navController: NavHostController = rememberNavController()) {
    val context = LocalContext.current
    val preferences = remember { ServiceLocator.preferences(context) }
    val onboardingComplete by preferences.onboardingComplete.collectAsState(initial = null)

    var launchedRecordingFromIntent by remember { mutableStateOf(false) }

    // Onboarding gates every other destination. No recording happens before
    // consent per ARCHITECTURE_PLAN.md section 5 (Onboarding/consent).
    val startDestination = if (onboardingComplete == true) Destinations.HOME else Destinations.ONBOARDING

    if (onboardingComplete == null) return // preferences not loaded yet

    NavHost(navController = navController, startDestination = startDestination) {
        composable(Destinations.ONBOARDING) {
            OnboardingScreen(onContinue = {
                navController.navigate(Destinations.HOME) {
                    popUpTo(Destinations.ONBOARDING) { inclusive = true }
                }
            })
        }
        composable(Destinations.HOME) {
            HomeScreen(
                onRecordToday = { navController.navigate(Destinations.RECORDING) },
                onOpenHistory = { navController.navigate(Destinations.HISTORY) },
                onOpenSettings = { navController.navigate(Destinations.SETTINGS) },
            )
        }
        composable(Destinations.HISTORY) {
            HistoryScreen(onBack = { navController.popBackStack() })
        }
        composable(Destinations.SETTINGS) {
            SettingsScreen(onBack = { navController.popBackStack() })
        }
        composable(Destinations.RECORDING) {
            RecordingScreen(onDone = { navController.popBackStack(Destinations.HOME, false) })
        }
    }

    LaunchedEffect(startWithRecording, onboardingComplete) {
        if (startWithRecording && onboardingComplete == true && !launchedRecordingFromIntent) {
            launchedRecordingFromIntent = true
            navController.navigate(Destinations.RECORDING)
        }
    }
}
