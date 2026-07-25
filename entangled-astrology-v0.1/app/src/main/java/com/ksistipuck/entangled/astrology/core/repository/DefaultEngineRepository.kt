package com.ksistipuck.entangled.astrology.core.repository

import com.ksistipuck.entangled.astrology.core.model.*
import com.ksistipuck.entangled.astrology.core.network.AstrologyEngine
import com.ksistipuck.entangled.astrology.core.settings.SettingsRepository
import com.ksistipuck.entangled.astrology.core.validation.EngineResponseValidator
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first

class DefaultEngineRepository(
    private val engine: AstrologyEngine,
    private val settingsRepository: SettingsRepository,
) : EngineRepository {
    private val mutableConnection = MutableStateFlow<EngineConnectionState>(EngineConnectionState.Unconfigured)
    override val connectionState = mutableConnection

    override suspend fun testConnection(): Result<EngineConnectionState.Connected> = runCatching {
        val baseUrl = requireBaseUrl()
        mutableConnection.value = EngineConnectionState.Checking
        val connected = EngineConnectionState.Connected(
            health = engine.health(baseUrl),
            identity = engine.identity(baseUrl),
            capabilities = engine.capabilities(baseUrl),
        )
        mutableConnection.value = connected
        connected
    }.onFailure { mutableConnection.value = EngineConnectionState.Failed(it.message ?: "Connection failed") }

    override suspend fun currentField(request: CurrentFieldRequest) = call {
        EngineResponseValidator.validateCurrentField(engine.currentField(it, request))
    }

    override suspend fun timeline(request: TimelineRequest) = call { engine.timeline(it, request) }
    override suspend fun natalChart(request: NatalChartRequest) = call { engine.natalChart(it, request) }
    override suspend fun placeResonance(request: PlaceResonanceRequest) = call { engine.placeResonance(it, request) }
    override suspend fun generateReport(request: ReportRequest) = call { engine.generateReport(it, request) }

    private suspend fun <T> call(block: suspend (String) -> T): Result<T> = runCatching { block(requireBaseUrl()) }

    private suspend fun requireBaseUrl(): String {
        val value = settingsRepository.settings.first().engineBaseUrl
        require(BaseUrlValidator.isValid(value)) { "Configure a valid engine URL before calculating." }
        return value.trimEnd('/')
    }
}

object BaseUrlValidator {
    fun isValid(value: String): Boolean {
        val trimmed = value.trim()
        return (trimmed.startsWith("https://") || trimmed.startsWith("http://")) &&
            trimmed.length > 10 && !trimmed.contains(' ')
    }
}
