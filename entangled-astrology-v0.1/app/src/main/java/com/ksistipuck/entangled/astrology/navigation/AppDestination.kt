package com.ksistipuck.entangled.astrology.navigation

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.outlined.*
import androidx.compose.ui.graphics.vector.ImageVector

sealed class AppDestination(val route: String, val label: String, val icon: ImageVector) {
    data object Today : AppDestination("today", "Today", Icons.Outlined.Explore)
    data object Timeline : AppDestination("timeline", "Timeline", Icons.Outlined.Timeline)
    data object Chart : AppDestination("chart", "Chart", Icons.Outlined.AutoGraph)
    data object Places : AppDestination("places", "Places", Icons.Outlined.Public)
    data object Library : AppDestination("library", "Library", Icons.Outlined.LocalLibrary)
    data object Onboarding : AppDestination("onboarding", "Profile", Icons.Outlined.PersonAdd)
    data object Settings : AppDestination("settings", "Settings", Icons.Outlined.Settings)
    data object Ecosystem : AppDestination("ecosystem", "Entangled", Icons.Outlined.Hub)

    companion object { val bottom = listOf(Today, Timeline, Chart, Places, Library) }
}
