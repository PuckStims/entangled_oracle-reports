package com.ksistipuck.entangled.astrology.core.settings

import android.content.Context
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.ksistipuck.entangled.astrology.core.model.BirthProfile
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json

private val Context.dataStore by preferencesDataStore("entangled_settings")

class SettingsRepository(private val context: Context) {
    private val json = Json { ignoreUnknownKeys = false; explicitNulls = false }

    val settings: Flow<AppSettings> = context.dataStore.data.map { prefs ->
        AppSettings(
            engineBaseUrl = prefs[Keys.ENGINE_URL].orEmpty(),
            profile = prefs[Keys.PROFILE_JSON]?.let { runCatching { json.decodeFromString<BirthProfile>(it) }.getOrNull() },
            reducedMotion = prefs[Keys.REDUCED_MOTION] ?: false,
            lowStimulation = prefs[Keys.LOW_STIMULATION] ?: false,
            highContrast = prefs[Keys.HIGH_CONTRAST] ?: false,
            textScale = prefs[Keys.TEXT_SCALE] ?: 1f,
        )
    }

    suspend fun setEngineBaseUrl(value: String) = context.dataStore.edit { it[Keys.ENGINE_URL] = value.trim() }
    suspend fun saveProfile(profile: BirthProfile) = context.dataStore.edit { it[Keys.PROFILE_JSON] = json.encodeToString(profile) }
    suspend fun clearProfile() = context.dataStore.edit { it.remove(Keys.PROFILE_JSON) }
    suspend fun setReducedMotion(value: Boolean) = context.dataStore.edit { it[Keys.REDUCED_MOTION] = value }
    suspend fun setLowStimulation(value: Boolean) = context.dataStore.edit { it[Keys.LOW_STIMULATION] = value }
    suspend fun setHighContrast(value: Boolean) = context.dataStore.edit { it[Keys.HIGH_CONTRAST] = value }
    suspend fun setTextScale(value: Float) = context.dataStore.edit { it[Keys.TEXT_SCALE] = value.coerceIn(0.9f, 1.4f) }

    private object Keys {
        val ENGINE_URL = stringPreferencesKey("engine_url")
        val PROFILE_JSON = stringPreferencesKey("profile_json")
        val REDUCED_MOTION = booleanPreferencesKey("reduced_motion")
        val LOW_STIMULATION = booleanPreferencesKey("low_stimulation")
        val HIGH_CONTRAST = booleanPreferencesKey("high_contrast")
        val TEXT_SCALE = floatPreferencesKey("text_scale")
    }
}

data class AppSettings(
    val engineBaseUrl: String,
    val profile: BirthProfile?,
    val reducedMotion: Boolean,
    val lowStimulation: Boolean,
    val highContrast: Boolean,
    val textScale: Float,
)
