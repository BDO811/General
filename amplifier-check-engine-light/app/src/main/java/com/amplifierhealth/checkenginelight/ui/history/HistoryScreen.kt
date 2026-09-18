package com.amplifierhealth.checkenginelight.ui.history

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.HorizontalDivider
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import com.amplifierhealth.checkenginelight.data.local.CheckStatus
import com.amplifierhealth.checkenginelight.data.local.DailyCheckEntity
import com.amplifierhealth.checkenginelight.model.SignalLevel
import com.amplifierhealth.checkenginelight.ui.ServiceLocator
import com.amplifierhealth.checkenginelight.ui.theme.SignalGray
import com.amplifierhealth.checkenginelight.ui.theme.SignalGreen
import com.amplifierhealth.checkenginelight.ui.theme.SignalRed
import com.amplifierhealth.checkenginelight.ui.theme.SignalYellow
import java.time.format.DateTimeFormatter

/**
 * Reverse-chronological light + score only. No raw biomarker table, no
 * `vocal_features`. See ARCHITECTURE_PLAN.md section 5 (UI) and
 * docs/PHASE_0_SPEC.md section 5.
 */
@Composable
fun HistoryScreen(onBack: () -> Unit) {
    val context = LocalContext.current
    val repository = remember { ServiceLocator.repository(context) }
    val history by repository.observeHistory(90).collectAsState(initial = emptyList())
    val dateFormatter = remember { DateTimeFormatter.ofPattern("EEE, MMM d") }

    Column(modifier = Modifier.fillMaxSize().padding(24.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("History", style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = onBack) { Text("Back") }
        }

        LazyColumn {
            items(history) { entity ->
                HistoryRow(entity, dateFormatter)
                HorizontalDivider()
            }
        }
    }
}

@Composable
private fun HistoryRow(entity: DailyCheckEntity, dateFormatter: DateTimeFormatter) {
    Row(
        modifier = Modifier.fillMaxWidth().padding(vertical = 12.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Column {
            Text(entity.localDate.format(dateFormatter), style = MaterialTheme.typography.bodyLarge)
            Text(labelFor(entity), style = MaterialTheme.typography.bodyMedium)
        }
        androidx.compose.foundation.layout.Box(
            modifier = Modifier.size(24.dp).background(colorFor(entity), CircleShape),
        )
    }
}

private fun labelFor(entity: DailyCheckEntity): String = when {
    entity.status != CheckStatus.DONE -> entity.status.name.lowercase().replace('_', ' ')
    entity.audioQualityIssue != null -> "retry needed"
    else -> when (SignalLevel.fromApi(entity.level, entity.audioQualityIssue)) {
        SignalLevel.GREEN -> "green"
        SignalLevel.YELLOW -> "yellow"
        SignalLevel.RED -> "red"
        SignalLevel.GRAY -> "inconclusive"
    }
}

private fun colorFor(entity: DailyCheckEntity): Color {
    if (entity.status != CheckStatus.DONE) return SignalGray
    return when (SignalLevel.fromApi(entity.level, entity.audioQualityIssue)) {
        SignalLevel.GREEN -> SignalGreen
        SignalLevel.YELLOW -> SignalYellow
        SignalLevel.RED -> SignalRed
        SignalLevel.GRAY -> SignalGray
    }
}
