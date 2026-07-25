package com.ksistipuck.entangled.astrology.feature.onboarding

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.ksistipuck.entangled.astrology.app.AppViewModel
import com.ksistipuck.entangled.astrology.core.designsystem.ScreenTitle
import com.ksistipuck.entangled.astrology.core.model.BirthProfile
import com.ksistipuck.entangled.astrology.core.model.BirthTimeConfidence

@Composable
fun OnboardingScreen(existing: BirthProfile?, viewModel: AppViewModel, navController: NavController) {
    var name by remember { mutableStateOf(existing?.displayName.orEmpty()) }
    var date by remember { mutableStateOf(existing?.localDate.orEmpty()) }
    var time by remember { mutableStateOf(existing?.localTime.orEmpty()) }
    var location by remember { mutableStateOf(existing?.locationName.orEmpty()) }
    var timeZone by remember { mutableStateOf(existing?.timeZoneId.orEmpty()) }
    var confidence by remember { mutableStateOf(existing?.birthTimeConfidence ?: BirthTimeConfidence.EXACT_RECORD) }
    val valid = name.isNotBlank() && date.isNotBlank() && location.isNotBlank() && timeZone.isNotBlank()

    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        ScreenTitle("Birth profile", "Anchor the chart", "Your birth data remains on this device until a calculation is explicitly sent to the configured engine.")
        OutlinedTextField(name, { name = it }, label = { Text("Name or profile label") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(date, { date = it }, label = { Text("Birth date · YYYY-MM-DD") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(time, { time = it }, label = { Text("Birth time · HH:MM") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(location, { location = it }, label = { Text("Birth location") }, modifier = Modifier.fillMaxWidth())
        OutlinedTextField(timeZone, { timeZone = it }, label = { Text("IANA time zone · America/Chicago") }, modifier = Modifier.fillMaxWidth())
        Text("Birth-time confidence", style = MaterialTheme.typography.titleMedium)
        BirthTimeConfidence.entries.forEach { option ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                RadioButton(selected = confidence == option, onClick = { confidence = option })
                Text(option.name.replace('_', ' ').lowercase().replaceFirstChar { it.uppercase() }, modifier = Modifier.padding(top = 12.dp))
            }
        }
        Button(
            enabled = valid,
            modifier = Modifier.fillMaxWidth(),
            onClick = {
                val profile = viewModel.createProfile(name, date, time, location, timeZone, confidence)
                viewModel.saveProfile(profile)
                navController.popBackStack()
            },
        ) { Text("Save profile") }
        Text("Coordinates are intentionally absent from manual entry in v0.1. Codex should connect a real geocoder or require verified coordinates before calculations that need them.", style = MaterialTheme.typography.bodySmall)
    }
}
