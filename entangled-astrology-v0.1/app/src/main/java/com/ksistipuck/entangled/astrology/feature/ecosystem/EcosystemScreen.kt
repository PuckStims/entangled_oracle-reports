package com.ksistipuck.entangled.astrology.feature.ecosystem

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.unit.dp
import com.ksistipuck.entangled.astrology.core.designsystem.*
import com.ksistipuck.entangled.astrology.core.ecosystem.EntangledAppRegistry

@Composable
fun EcosystemScreen() {
    val uriHandler = LocalUriHandler.current
    Column(
        Modifier.fillMaxSize().verticalScroll(rememberScrollState()).padding(24.dp),
        verticalArrangement = Arrangement.spacedBy(18.dp),
    ) {
        ScreenTitle("Entangled", "One ecosystem, distinct practices", "Astrology is one doorway into the wider Entangled platform.")
        EntangledAppRegistry.apps.forEach { app ->
            EntangledCard(Modifier.fillMaxWidth()) {
                Text(app.label, style = MaterialTheme.typography.titleLarge)
                Text(app.description, color = EntangledColors.Muted)
                when {
                    app.isCurrent -> Text("OPEN", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Verdigris)
                    app.launchUri != null -> Button(onClick = { uriHandler.openUri(app.launchUri) }) { Text("Open app") }
                    else -> Text("LINK TARGET NOT CONFIGURED", style = MaterialTheme.typography.labelSmall, color = EntangledColors.Amethyst)
                }
            }
        }
    }
}
