package com.amplifierhealth.checkenginelight.ui.home

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
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

/**
 * One home screen: today's light plus a short trend line. Deliberately not
 * a dashboard. See ARCHITECTURE_PLAN.md section 5 (UI) and section 1.
 */
@Composable
fun HomeScreen(onRecordToday: () -> Unit, onOpenHistory: () -> Unit, onOpenSettings: () -> Unit) {
    val context = LocalContext.current
    val repository = remember { ServiceLocator.repository(context) }
    val latest by repository.observeLatest().collectAsState(initial = null)
    val history by repository.observeHistory(14).collectAsState(initial = emptyList())

    Column(modifier = Modifier.fillMaxSize().padding(24.dp)) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
        ) {
            Text("Today", style = MaterialTheme.typography.headlineMedium)
            TextButton(onClick = onOpenSettings) { Text("Settings") }
        }

        Spacer(Modifier.height(32.dp))

        Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
            CheckEngineLight(entity = latest)
        }

        Spacer(Modifier.height(24.dp))

        Box(modifier = Modifier.fillMaxWidth(), contentAlignment = Alignment.Center) {
            Text(statusLine(latest), style = MaterialTheme.typography.bodyLarge)
        }

        Spacer(Modifier.height(32.dp))

        if (latest == null || latest?.status == CheckStatus.FAILED) {
            Button(onClick = onRecordToday, modifier = Modifier.fillMaxWidth()) {
                Text(if (latest?.status == CheckStatus.FAILED) "Retry today's check" else "Record today's check")
            }
        }

        Spacer(Modifier.height(40.dp))

        Text("Last 14 days", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(12.dp))
        TrendSparkline(history = history, modifier = Modifier.fillMaxWidth().height(48.dp))

        Spacer(Modifier.height(24.dp))
        TextButton(onClick = onOpenHistory) { Text("View history") }
    }
}

@Composable
private fun CheckEngineLight(entity: DailyCheckEntity?) {
    val color = colorForStatus(entity)
    Box(
        modifier = Modifier
            .size(160.dp)
            .background(color, CircleShape),
    )
}

private fun statusLine(entity: DailyCheckEntity?): String = when {
    entity == null -> "Not recorded yet today."
    entity.status == CheckStatus.UPLOADING || entity.status == CheckStatus.PROCESSING -> "Processing today's check"
    entity.status == CheckStatus.FAILED -> "Something went wrong. Retry when you're ready."
    entity.audioQualityIssue != null -> "We couldn't get a clean read. Give it another try."
    else -> "Today's check is in."
}

private fun colorForStatus(entity: DailyCheckEntity?): Color {
    if (entity == null || entity.status != CheckStatus.DONE) return SignalGray
    return when (SignalLevel.fromApi(entity.level, entity.audioQualityIssue)) {
        SignalLevel.GREEN -> SignalGreen
        SignalLevel.YELLOW -> SignalYellow
        SignalLevel.RED -> SignalRed
        SignalLevel.GRAY -> SignalGray
    }
}

@Composable
private fun TrendSparkline(history: List<DailyCheckEntity>, modifier: Modifier = Modifier) {
    val ordered = remember(history) { history.sortedBy { it.localDate } }
    Canvas(modifier = modifier) {
        if (ordered.isEmpty()) return@Canvas
        val stepX = size.width / (ordered.size.coerceAtLeast(2) - 1).toFloat().coerceAtLeast(1f)
        ordered.forEachIndexed { index, entity ->
            val x = stepX * index
            val color = colorForStatus(entity)
            drawCircle(color = color, radius = 5f, center = Offset(x, size.height / 2f))
        }
    }
}
