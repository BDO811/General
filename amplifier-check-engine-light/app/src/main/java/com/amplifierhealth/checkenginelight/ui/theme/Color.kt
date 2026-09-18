package com.amplifierhealth.checkenginelight.ui.theme

import androidx.compose.ui.graphics.Color

// Amplifier Health brand palette.
val BackgroundNearBlack = Color(0xFF050505)
val SurfaceDark = Color(0xFF0A0A0A)
val SurfaceElevated = Color(0xFF18181B)
val AccentCyan = Color(0xFF22D3EE)
val AccentEmerald = Color(0xFF10B981)
val TextPrimary = Color(0xFFFAFAFA)
val TextSecondary = Color(0xB3FFFFFF)
val GridOverlay = Color(0x14FFFFFF)

// Check-engine light states (ARCHITECTURE_PLAN.md section 5, Result handling).
// Intentionally distinct from the brand accents so the light itself always
// reads as a status signal, never as decoration.
val SignalGreen = Color(0xFF10B981)
val SignalYellow = Color(0xFFF5B700)
val SignalRed = Color(0xFFEF4444)
val SignalGray = Color(0xFF6B7280)
