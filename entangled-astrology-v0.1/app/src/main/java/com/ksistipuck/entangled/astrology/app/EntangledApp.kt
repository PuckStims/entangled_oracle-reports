package com.ksistipuck.entangled.astrology.app

import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.systemBarsPadding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.Hub
import androidx.compose.material.icons.outlined.Settings
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.runtime.getValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalDensity
import androidx.compose.ui.unit.Density
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.ksistipuck.entangled.astrology.core.designsystem.EntangledTheme
import com.ksistipuck.entangled.astrology.feature.chart.ChartScreen
import com.ksistipuck.entangled.astrology.feature.ecosystem.EcosystemScreen
import com.ksistipuck.entangled.astrology.feature.library.LibraryScreen
import com.ksistipuck.entangled.astrology.feature.onboarding.OnboardingScreen
import com.ksistipuck.entangled.astrology.feature.places.PlacesScreen
import com.ksistipuck.entangled.astrology.feature.settings.SettingsScreen
import com.ksistipuck.entangled.astrology.feature.timeline.TimelineScreen
import com.ksistipuck.entangled.astrology.feature.today.TodayScreen
import com.ksistipuck.entangled.astrology.navigation.AppDestination

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun EntangledApp(container: AppContainer) {
    val appViewModel: AppViewModel = viewModel(factory = AppViewModel.Factory(container))
    val state by appViewModel.uiState.collectAsStateWithLifecycle()
    val navController = rememberNavController()
    val currentEntry by navController.currentBackStackEntryAsState()
    val currentRoute = currentEntry?.destination?.route

    val baseDensity = LocalDensity.current
    val textScale = state.settings?.textScale ?: 1f

    CompositionLocalProvider(
        LocalDensity provides Density(baseDensity.density, baseDensity.fontScale * textScale),
    ) {
        EntangledTheme(
            highContrast = state.settings?.highContrast ?: false,
            lowStimulation = state.settings?.lowStimulation ?: false,
        ) {
            Scaffold(
                modifier = Modifier.systemBarsPadding(),
                topBar = {
                CenterAlignedTopAppBar(
                    title = {
                        TextButton(onClick = { navController.navigate(AppDestination.Ecosystem.route) }) {
                            Text("ENTANGLED  /  ASTROLOGY", style = MaterialTheme.typography.labelSmall)
                        }
                    },
                    actions = {
                        IconButton(onClick = { navController.navigate(AppDestination.Ecosystem.route) }) {
                            Icon(Icons.Outlined.Hub, contentDescription = "Entangled ecosystem")
                        }
                        IconButton(onClick = { navController.navigate(AppDestination.Settings.route) }) {
                            Icon(Icons.Outlined.Settings, contentDescription = "Settings")
                        }
                    },
                    colors = TopAppBarDefaults.topAppBarColors(containerColor = MaterialTheme.colorScheme.background),
                )
                },
                bottomBar = {
                if (currentRoute in AppDestination.bottom.map { it.route }) {
                    NavigationBar(containerColor = MaterialTheme.colorScheme.background) {
                        AppDestination.bottom.forEach { destination ->
                            NavigationBarItem(
                                selected = currentRoute == destination.route,
                                onClick = { navController.navigate(destination.route) { launchSingleTop = true } },
                                icon = { Icon(destination.icon, contentDescription = destination.label) },
                                label = { Text(destination.label) },
                            )
                        }
                    }
                }
                },
            ) { padding ->
                Box(Modifier.padding(padding)) {
                NavHost(navController, startDestination = AppDestination.Today.route) {
                    composable(AppDestination.Today.route) { TodayScreen(state, appViewModel, navController) }
                    composable(AppDestination.Timeline.route) { TimelineScreen(state, appViewModel, navController) }
                    composable(AppDestination.Chart.route) { ChartScreen(state, appViewModel, navController) }
                    composable(AppDestination.Places.route) { PlacesScreen(state, appViewModel, navController) }
                    composable(AppDestination.Library.route) { LibraryScreen(state, navController) }
                    composable(AppDestination.Onboarding.route) { OnboardingScreen(state.settings?.profile, appViewModel, navController) }
                    composable(AppDestination.Settings.route) { SettingsScreen(state, appViewModel, navController) }
                    composable(AppDestination.Ecosystem.route) { EcosystemScreen() }
                }
                }
            }
        }
    }
}
