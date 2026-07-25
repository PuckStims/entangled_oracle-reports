package com.ksistipuck.entangled.astrology.core.designsystem

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

object EntangledColors {
    val Void = Color(0xFF090A12)
    val Surface = Color(0xFF11131E)
    val Raised = Color(0xFF181B29)
    val Bone = Color(0xFFEDE7DB)
    val Muted = Color(0xFFA8A1AE)
    val Verdigris = Color(0xFF0FD6A5)
    val QuietVerdigris = Color(0xFF75BDAA)
    val Amethyst = Color(0xFFC29AFF)
    val QuietAmethyst = Color(0xFFAA9DBD)
    val Rose = Color(0xFFEB7AAE)
    val Gold = Color(0xFFE0BD58)
    val Error = Color(0xFFFF8C8C)
}

private fun scheme(highContrast: Boolean, lowStimulation: Boolean) = darkColorScheme(
    primary = if (lowStimulation) EntangledColors.QuietVerdigris else EntangledColors.Verdigris,
    secondary = if (lowStimulation) EntangledColors.QuietAmethyst else EntangledColors.Amethyst,
    tertiary = if (lowStimulation) EntangledColors.QuietAmethyst else EntangledColors.Rose,
    background = EntangledColors.Void,
    surface = EntangledColors.Surface,
    surfaceVariant = EntangledColors.Raised,
    onPrimary = EntangledColors.Void,
    onBackground = EntangledColors.Bone,
    onSurface = EntangledColors.Bone,
    onSurfaceVariant = if (highContrast) EntangledColors.Bone else EntangledColors.Muted,
    outline = if (highContrast) EntangledColors.Bone else EntangledColors.Muted,
    error = EntangledColors.Error,
)

@Composable
fun EntangledTheme(
    highContrast: Boolean = false,
    lowStimulation: Boolean = false,
    content: @Composable () -> Unit,
) {
    MaterialTheme(
        colorScheme = scheme(highContrast, lowStimulation),
        typography = MaterialTheme.typography.copy(
            displaySmall = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Normal, fontSize = 34.sp, lineHeight = 40.sp),
            headlineMedium = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Normal, fontSize = 27.sp, lineHeight = 33.sp),
            titleLarge = TextStyle(fontFamily = FontFamily.Serif, fontWeight = FontWeight.Medium, fontSize = 22.sp),
            titleMedium = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.SemiBold, fontSize = 16.sp),
            bodyLarge = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Normal, fontSize = 16.sp, lineHeight = 24.sp),
            bodyMedium = TextStyle(fontFamily = FontFamily.SansSerif, fontWeight = FontWeight.Normal, fontSize = 14.sp, lineHeight = 21.sp),
            labelSmall = TextStyle(fontFamily = FontFamily.Monospace, fontWeight = FontWeight.Medium, fontSize = 11.sp, letterSpacing = 0.7.sp),
        ),
        content = content,
    )
}
