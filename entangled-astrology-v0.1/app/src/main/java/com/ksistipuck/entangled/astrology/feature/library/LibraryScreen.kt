package com.ksistipuck.entangled.astrology.feature.library

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.ksistipuck.entangled.astrology.app.AppUiState
import com.ksistipuck.entangled.astrology.core.designsystem.*
import com.ksistipuck.entangled.astrology.navigation.AppDestination

@Composable
fun LibraryScreen(state: AppUiState, navController: NavController) {
    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        ScreenTitle("Owned work", "Your report library", "Reports are durable objects—not expiring credits or disposable readings.")
        val reports = listOf(
            "Year Ahead" to "A full timing architecture for the coming year.",
            "Soul Ecosystem" to "Natal systems, relationships, and internal ecology.",
            "Personal Forecast" to "Focused calculated timing for a selected period.",
            "Relationship Field" to "Resonance, friction, reciprocity, and timing between charts.",
            "Place Resonance" to "A single-location locational astrology report.",
            "Between Places" to "A comparison across selected locations.",
        )
        reports.forEach { (title, summary) ->
            EntangledCard(Modifier.fillMaxWidth()) {
                Text(title, style = MaterialTheme.typography.titleLarge)
                Text(summary, color = EntangledColors.Muted)
                Text("Available when declared by the connected engine", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
            }
        }
        if (state.settings?.profile == null) {
            Button(onClick = { navController.navigate(AppDestination.Onboarding.route) }) { Text("Create profile") }
        }
    }
}
