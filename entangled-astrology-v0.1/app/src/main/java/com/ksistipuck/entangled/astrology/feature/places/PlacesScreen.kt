package com.ksistipuck.entangled.astrology.feature.places

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.ksistipuck.entangled.astrology.app.*
import com.ksistipuck.entangled.astrology.core.designsystem.*
import com.ksistipuck.entangled.astrology.core.model.GeoPoint
import com.ksistipuck.entangled.astrology.core.model.PlaceInput
import com.ksistipuck.entangled.astrology.core.repository.EngineConnectionState
import com.ksistipuck.entangled.astrology.navigation.AppDestination

@Composable
fun PlacesScreen(state: AppUiState, viewModel: AppViewModel, navController: NavController) {
    var name by remember { mutableStateOf("") }
    var latitude by remember { mutableStateOf("") }
    var longitude by remember { mutableStateOf("") }
    var timeZone by remember { mutableStateOf("") }
    val place = runCatching {
        PlaceInput(name.trim(), GeoPoint(latitude.toDouble(), longitude.toDouble()), timeZone.trim())
    }.getOrNull()?.takeIf { it.name.isNotBlank() && it.timeZoneId.isNotBlank() }

    Column(Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp), verticalArrangement = Arrangement.spacedBy(18.dp)) {
        ScreenTitle("Place resonance", "How location changes the chart", "Verified coordinates are required; v0.1 never guesses a place from a name.")
        if (state.settings?.profile == null) {
            Button(onClick = { navController.navigate(AppDestination.Onboarding.route) }) { Text("Create birth profile") }
            return@Column
        }
        OutlinedTextField(name, { name = it }, label = { Text("Place name") }, modifier = Modifier.fillMaxWidth())
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(latitude, { latitude = it }, label = { Text("Latitude") }, modifier = Modifier.weight(1f))
            OutlinedTextField(longitude, { longitude = it }, label = { Text("Longitude") }, modifier = Modifier.weight(1f))
        }
        OutlinedTextField(timeZone, { timeZone = it }, label = { Text("IANA time zone") }, modifier = Modifier.fillMaxWidth())
        val connection = state.connection
        if (connection !is EngineConnectionState.Connected) {
            EmptyEngineState("Engine required", "Connect Entangled Oracle before calculating Place Resonance.", { navController.navigate(AppDestination.Settings.route) })
        } else if (!connection.capabilities.supportsPlaceResonance) {
            EntangledCard(Modifier.fillMaxWidth()) {
                Text("Place Resonance is not exposed yet", style = MaterialTheme.typography.titleLarge)
                Text("The backend can generate location-service reports, but the structured mobile Place Resonance endpoint remains paused until source-to-output parity is documented.", color = EntangledColors.Muted)
            }
        } else {
            Button(enabled = place != null, onClick = { place?.let(viewModel::loadPlace) }, modifier = Modifier.fillMaxWidth()) { Text("Calculate Place Resonance") }
            when (val result = state.placeResonance) {
                DataState.Idle -> Text("No place calculation has been requested.", color = EntangledColors.Muted)
                DataState.Loading -> CircularProgressIndicator()
                is DataState.Error -> Text(result.message, color = MaterialTheme.colorScheme.error)
                is DataState.Ready -> {
                    EntangledCard(Modifier.fillMaxWidth()) {
                        Text(result.value.headline, style = MaterialTheme.typography.titleLarge)
                        Text(result.value.summary)
                        result.value.nearestLines.forEach { line ->
                            Text("${line.planet} ${line.angle} · ${line.distanceKm} km${if (line.birthTimeSensitive) " · birth-time sensitive" else ""}")
                        }
                    }
                    ProvenanceBlock(result.value.provenance.engineVersion, result.value.provenance.calculationModules, result.value.provenance.warnings)
                }
            }
        }
    }
}
