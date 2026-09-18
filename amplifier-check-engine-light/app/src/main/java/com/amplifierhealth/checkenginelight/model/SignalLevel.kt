package com.amplifierhealth.checkenginelight.model

/**
 * The check-engine light. This is the only vocabulary the UI is allowed to
 * show; never the raw LAM `level`/`score`/`description` fields directly.
 * See ARCHITECTURE_PLAN.md section 5 (Result handling).
 */
enum class SignalLevel {
    GREEN,
    YELLOW,
    RED,
    GRAY;

    companion object {
        /**
         * Maps an Amplifier LAM `signal.level` string to a check-engine light
         * color. `audioQualityIssue` overrides everything else to gray/retry,
         * since a bad capture should never be shown as a health reading.
         */
        fun fromApi(level: String?, audioQualityIssue: String?): SignalLevel {
            if (audioQualityIssue != null) return GRAY
            return when (level?.lowercase()) {
                "none", "low" -> GREEN
                "consider", "moderate" -> YELLOW
                "elevated" -> RED
                "inconclusive" -> GRAY
                else -> GRAY
            }
        }
    }
}
