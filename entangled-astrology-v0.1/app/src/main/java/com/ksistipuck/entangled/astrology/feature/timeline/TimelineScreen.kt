package com.ksistipuck.entangled.astrology.feature.timeline

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
import com.ksistipuck.entangled.astrology.core.repository.EngineConnectionState
import com.ksistipuck.entangled.astrology.navigation.AppDestination

@Composable
fun TimelineScreen(state: AppUiState, viewModel: AppViewModel, navController: NavController) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        ScreenTitle("Timing", "Your astrological timeline", "Applying, exact, separating, and longer background cycles—without invented urgency.")
        if (state.settings?.profile == null) {
            Button(onClick = { navController.navigate(AppDestination.Onboarding.route) }) { Text("Create birth profile") }
        } else if (state.connection !is EngineConnectionState.Connected) {
            EmptyEngineState("Engine required", "Connect Entangled Oracle to calculate a timeline.", { navController.navigate(AppDestination.Settings.route) })
        } else {
            DataStatePanel(state.timeline, "No timeline calculated", "Request the next 7 days from the real engine.", { viewModel.loadTimeline() }) { timeline ->
                timeline.events.sortedBy { it.exactAt ?: it.startsAt ?: "" }.forEach { event ->
                    EntangledCard(Modifier.fillMaxWidth()) {
                        Text(event.phase.uppercase(), style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
                        Text(event.title ?: listOfNotNull(event.movingBody, event.aspect, event.natalTarget).joinToString(" "), style = MaterialTheme.typography.titleMedium)
                        Text("START ${event.startsAt ?: "—"}\nPEAK ${event.exactAt ?: "—"}\nEND ${event.endsAt ?: "—"}", style = MaterialTheme.typography.labelSmall)
                    }
                }
                ProvenanceBlock(timeline.provenance.engineVersion, timeline.provenance.calculationModules, timeline.provenance.warnings)
            }
        }
    }
}
