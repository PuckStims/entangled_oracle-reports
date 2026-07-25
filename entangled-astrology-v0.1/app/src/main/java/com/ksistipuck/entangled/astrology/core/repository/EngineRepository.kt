package com.ksistipuck.entangled.astrology.core.repository

import com.ksistipuck.entangled.astrology.core.model.*
import kotlinx.coroutines.flow.Flow

sealed interface EngineConnectionState {
    data object Unconfigured : EngineConnectionState
    data object Checking : EngineConnectionState
    data class Connected(val health: EngineHealth, val identity: EngineIdentity, val capabilities: EngineCapabilities) : EngineConnectionState
    data class Failed(val message: String) : EngineConnectionState
}

interface EngineRepository {
    val connectionState: Flow<EngineConnectionState>
    suspend fun testConnection(): Result<EngineConnectionState.Connected>
    suspend fun currentField(request: CurrentFieldRequest): Result<CurrentField>
    suspend fun timeline(request: TimelineRequest): Result<TimelineResponse>
    suspend fun natalChart(request: NatalChartRequest): Result<NatalChart>
    suspend fun placeResonance(request: PlaceResonanceRequest): Result<PlaceResonance>
    suspend fun generateReport(request: ReportRequest): Result<ReportJob>
}
