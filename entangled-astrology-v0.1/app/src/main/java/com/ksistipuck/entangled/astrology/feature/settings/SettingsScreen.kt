package com.ksistipuck.entangled.astrology.feature.settings

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Slider
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.navigation.NavController
import com.ksistipuck.entangled.astrology.app.AppUiState
import com.ksistipuck.entangled.astrology.app.AppViewModel
import com.ksistipuck.entangled.astrology.core.designsystem.EntangledCard
import com.ksistipuck.entangled.astrology.core.designsystem.EntangledColors
import com.ksistipuck.entangled.astrology.core.designsystem.ScreenTitle
import com.ksistipuck.entangled.astrology.core.repository.EngineConnectionState
import com.ksistipuck.entangled.astrology.navigation.AppDestination

@Composable
fun SettingsScreen(state: AppUiState, viewModel: AppViewModel, navController: NavController) {
    var url by remember(state.settings?.engineBaseUrl) { mutableStateOf(state.settings?.engineBaseUrl.orEmpty()) }
    val settings = state.settings
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        ScreenTitle("Integration", "Engine & accessibility", "The app is useful only when its calculation source is explicit.")
        EntangledCard(Modifier.fillMaxWidth()) {
            Text("Entangled Oracle connection", style = MaterialTheme.typography.titleLarge)
            OutlinedTextField(
                value = url,
                onValueChange = { url = it },
                label = { Text("Backend URL") },
                supportingText = { Text("Real phone example: http://192.168.1.42:8000") },
                modifier = Modifier.fillMaxWidth(),
            )
            Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                Button(onClick = { viewModel.saveAndTestEngineUrl(url) }) { Text("Save and test") }
                OutlinedButton(onClick = { viewModel.testConnection() }) { Text("Retest saved URL") }
            }
            when (val connection = state.connection) {
                EngineConnectionState.Unconfigured -> Text("Not configured yet", color = EntangledColors.Muted)
                EngineConnectionState.Checking -> LinearProgressIndicator(Modifier.fillMaxWidth())
                is EngineConnectionState.Failed -> Text(connection.message, color = MaterialTheme.colorScheme.error)
                is EngineConnectionState.Connected -> {
                    Text("Connected: ${connection.identity.engine} ${connection.identity.engineVersion}", color = EntangledColors.Verdigris)
                    Text("Schema ${connection.identity.schemaVersion} / ${connection.capabilities.supportedTechniques.size} techniques")
                    if (state.settings?.profile == null) {
                        Button(onClick = { navController.navigate(AppDestination.Onboarding.route) }) { Text("Create profile") }
                    } else {
                        Button(onClick = { navController.navigate(AppDestination.Chart.route) }) { Text("View natal chart") }
                    }
                }
            }
        }
        EntangledCard(Modifier.fillMaxWidth()) {
            Text("Accessibility", style = MaterialTheme.typography.titleLarge)
            SettingSwitch("Reduced motion", settings?.reducedMotion ?: false, viewModel::setReducedMotion)
            SettingSwitch("Low-stimulation presentation", settings?.lowStimulation ?: false, viewModel::setLowStimulation)
            SettingSwitch("High contrast", settings?.highContrast ?: false, viewModel::setHighContrast)
            Text("Text scale ${"%.1f".format(settings?.textScale ?: 1f)}x")
            Slider(value = settings?.textScale ?: 1f, onValueChange = viewModel::setTextScale, valueRange = 0.9f..1.4f, steps = 4)
        }
        EntangledCard(Modifier.fillMaxWidth()) {
            Text("Privacy posture", style = MaterialTheme.typography.titleLarge)
            Text("Birth profiles and preferences are stored locally with DataStore. Calculation requests are sent only to the URL you configure. HTTP logging is disabled. Cloud backup is disabled for app data.", color = EntangledColors.Muted)
        }
    }
}

@Composable
private fun SettingSwitch(label: String, checked: Boolean, onChange: (Boolean) -> Unit) {
    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
        Text(label, modifier = Modifier.weight(1f))
        Switch(checked = checked, onCheckedChange = onChange)
    }
}
