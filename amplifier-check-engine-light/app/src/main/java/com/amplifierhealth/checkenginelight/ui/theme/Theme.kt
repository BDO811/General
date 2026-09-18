package com.amplifierhealth.checkenginelight.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

// Always dark: the near-black background is the product's identity, not a
// system-theme-following choice.
private val CheckEngineDarkColors = darkColorScheme(
    primary = AccentCyan,
    secondary = AccentEmerald,
    background = BackgroundNearBlack,
    surface = SurfaceDark,
    surfaceVariant = SurfaceElevated,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
)

@Composable
fun CheckEngineLightTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = CheckEngineDarkColors,
        typography = AppTypography,
        content = content,
    )
}
