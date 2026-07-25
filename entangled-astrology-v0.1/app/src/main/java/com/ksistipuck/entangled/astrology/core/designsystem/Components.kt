package com.ksistipuck.entangled.astrology.core.designsystem

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Cable
import androidx.compose.material.icons.outlined.ErrorOutline
import androidx.compose.material.icons.outlined.HourglassTop
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.ksistipuck.entangled.astrology.app.DataState

@Composable
fun EntangledCard(modifier: Modifier = Modifier, content: @Composable ColumnScope.() -> Unit) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(containerColor = EntangledColors.Surface),
        border = BorderStroke(1.dp, EntangledColors.Raised),
        shape = RoundedCornerShape(24.dp),
    ) { Column(Modifier.padding(20.dp), verticalArrangement = Arrangement.spacedBy(12.dp), content = content) }
}

@Composable
fun ScreenTitle(eyebrow: String, title: String, description: String? = null) {
    Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
        Text(eyebrow.uppercase(), style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
        Text(title, style = MaterialTheme.typography.headlineMedium)
        description?.let { Text(it, style = MaterialTheme.typography.bodyMedium, color = EntangledColors.Muted) }
    }
}

@Composable
fun EmptyEngineState(
    title: String,
    message: String,
    onConfigure: () -> Unit,
    modifier: Modifier = Modifier,
) {
    StatusCard(Icons.Outlined.Cable, title, message, "Configure engine", onConfigure, modifier)
}

@Composable
fun <T> DataStatePanel(
    state: DataState<T>,
    idleTitle: String,
    idleMessage: String,
    onLoad: () -> Unit,
    content: @Composable (T) -> Unit,
) {
    when (state) {
        DataState.Idle -> StatusCard(Icons.Outlined.HourglassTop, idleTitle, idleMessage, "Calculate", onLoad)
        DataState.Loading -> Box(Modifier.fillMaxWidth().padding(48.dp), contentAlignment = Alignment.Center) { CircularProgressIndicator() }
        is DataState.Error -> StatusCard(Icons.Outlined.ErrorOutline, "Calculation unavailable", state.message, "Try again", onLoad)
        is DataState.Ready -> content(state.value)
    }
}

@Composable
private fun StatusCard(
    icon: ImageVector,
    title: String,
    message: String,
    action: String,
    onAction: () -> Unit,
    modifier: Modifier = Modifier,
) {
    EntangledCard(modifier.fillMaxWidth()) {
        Icon(icon, contentDescription = null, tint = EntangledColors.Amethyst, modifier = Modifier.size(28.dp))
        Text(title, style = MaterialTheme.typography.titleLarge)
        Text(message, style = MaterialTheme.typography.bodyMedium, color = EntangledColors.Muted)
        Button(onClick = onAction) { Text(action) }
    }
}

@Composable
fun ProvenanceBlock(engineVersion: String, modules: List<String>, warnings: List<String>) {
    EntangledCard(Modifier.fillMaxWidth()) {
        Text("Calculation provenance", style = MaterialTheme.typography.titleMedium)
        Text("ENGINE $engineVersion", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
        modules.forEach { Text(it, style = MaterialTheme.typography.bodyMedium, fontFamily = androidx.compose.ui.text.font.FontFamily.Monospace) }
        warnings.forEach { Text("Warning: $it", color = MaterialTheme.colorScheme.error, style = MaterialTheme.typography.bodyMedium) }
    }
}
