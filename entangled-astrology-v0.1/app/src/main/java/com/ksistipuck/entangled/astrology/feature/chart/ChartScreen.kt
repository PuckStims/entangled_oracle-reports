package com.ksistipuck.entangled.astrology.feature.chart

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
fun ChartScreen(state: AppUiState, viewModel: AppViewModel, navController: NavController) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        ScreenTitle("Natal anchor", "Your chart, inspectable", "Placements and aspects are displayed only after the engine calculates them.")
        if (state.settings?.profile == null) {
            Button(onClick = { navController.navigate(AppDestination.Onboarding.route) }) { Text("Create birth profile") }
        } else if (state.connection !is EngineConnectionState.Connected) {
            EmptyEngineState("Engine required", "Connect the real calculation engine to produce a natal chart.", { navController.navigate(AppDestination.Settings.route) })
        } else {
            DataStatePanel(state.natalChart, "Chart not calculated", "Request a natal chart using the saved profile.", { viewModel.loadNatalChart() }) { chart ->
                EntangledCard(Modifier.fillMaxWidth()) {
                    Text("${chart.zodiac.uppercase()} · ${chart.houseSystem.uppercase()}", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
                    chart.placements.forEach { p ->
                        Text("${p.body}: ${"%.2f".format(p.degree)}° ${p.sign}${p.house?.let { ", house $it" } ?: ""}${if (p.retrograde) " ℞" else ""}")
                    }
                }
                EntangledCard(Modifier.fillMaxWidth()) {
                    Text("Aspects", style = MaterialTheme.typography.titleLarge)
                    chart.aspects.forEach { a -> Text("${a.pointA} ${a.aspect} ${a.pointB} · ${a.orbDegrees}°", style = MaterialTheme.typography.bodyMedium) }
                }
                ProvenanceBlock(chart.provenance.engineVersion, chart.provenance.calculationModules, chart.provenance.warnings)
            }
        }
    }
}
