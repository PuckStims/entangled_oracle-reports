package com.ksistipuck.entangled.astrology.feature.today

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.ksistipuck.entangled.astrology.app.*
import com.ksistipuck.entangled.astrology.core.designsystem.*
import com.ksistipuck.entangled.astrology.core.model.CurrentField
import com.ksistipuck.entangled.astrology.core.repository.EngineConnectionState
import com.ksistipuck.entangled.astrology.navigation.AppDestination

@Composable
fun TodayScreen(state: AppUiState, viewModel: AppViewModel, navController: NavController) {
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        ScreenTitle("Current field", "What is active now", "A structured view of timing, synthesis, and the calculations beneath it.")
        val profile = state.settings?.profile
        if (profile == null) {
            EntangledCard(Modifier.fillMaxWidth()) {
                Text("No birth profile", style = MaterialTheme.typography.titleLarge)
                Text("Add your real birth details before requesting calculations.", color = EntangledColors.Muted)
                Button(onClick = { navController.navigate(AppDestination.Onboarding.route) }) { Text("Create profile") }
            }
            return@Column
        }
        Text(profile.displayName, style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
        when (state.connection) {
            EngineConnectionState.Unconfigured, is EngineConnectionState.Failed -> EmptyEngineState(
                "Entangled Oracle is not connected",
                "Configure the backend URL. No chart or interpretation will be fabricated while the engine is unavailable.",
                { navController.navigate(AppDestination.Settings.route) },
            )
            EngineConnectionState.Checking -> CircularProgressIndicator()
            is EngineConnectionState.Connected -> DataStatePanel(
                state = state.currentField,
                idleTitle = "Ready for Current Field",
                idleMessage = "Request the current transit field from the connected Entangled Oracle backend.",
                onLoad = { viewModel.loadCurrentField() },
            ) { CurrentFieldContent(it) }
        }
    }
}

@Composable
private fun CurrentFieldContent(field: CurrentField) {
    val ordered = field.patterns.sortedBy { listOf("dominant", "supporting", "background").indexOf(it.role) }
    ordered.forEach { pattern ->
        EntangledCard(Modifier.fillMaxWidth()) {
            Text("${pattern.role.uppercase()} · ${pattern.stage.uppercase()}", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
            Text(pattern.title, style = MaterialTheme.typography.titleLarge)
            Text(pattern.summary, style = MaterialTheme.typography.bodyLarge)
            if (pattern.orientation.isNotEmpty()) {
                HorizontalDivider()
                pattern.orientation.forEach { Text("• $it", color = EntangledColors.Muted) }
            }
            Text("Supported by ${pattern.eventIds.size} calculated event(s)", style = MaterialTheme.typography.labelSmall)
        }
    }
    field.events.forEach { event ->
        EntangledCard(Modifier.fillMaxWidth()) {
            Text("${event.technique.uppercase()} · ${event.phase.uppercase()}", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Amethyst)
            Text(event.title ?: listOfNotNull(event.movingBody, event.aspect, event.natalTarget).joinToString(" "), style = MaterialTheme.typography.titleMedium)
            event.interpretation?.let { Text(it, color = EntangledColors.Muted) }
            Text("ORB ${event.orbDegrees ?: "—"}° · EXACT ${event.exactAt ?: "not supplied"}", style = MaterialTheme.typography.labelSmall)
            if (event.birthTimeSensitive) Text("Birth-time sensitive", color = EntangledColors.Gold, style = MaterialTheme.typography.labelSmall)
        }
    }
    ProvenanceBlock(field.provenance.engineVersion, field.provenance.calculationModules, field.provenance.warnings)
}
