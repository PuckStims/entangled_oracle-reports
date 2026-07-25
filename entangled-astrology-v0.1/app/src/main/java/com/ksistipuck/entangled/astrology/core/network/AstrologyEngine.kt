package com.ksistipuck.entangled.astrology.core.network

import com.ksistipuck.entangled.astrology.core.model.*

interface AstrologyEngine {
    suspend fun health(baseUrl: String): EngineHealth
    suspend fun identity(baseUrl: String): EngineIdentity
    suspend fun capabilities(baseUrl: String): EngineCapabilities
    suspend fun validateProfile(baseUrl: String, request: ProfileValidationRequest): ProfileValidationResponse
    suspend fun natalChart(baseUrl: String, request: NatalChartRequest): NatalChart
    suspend fun currentField(baseUrl: String, request: CurrentFieldRequest): CurrentField
    suspend fun timeline(baseUrl: String, request: TimelineRequest): TimelineResponse
    suspend fun placeResonance(baseUrl: String, request: PlaceResonanceRequest): PlaceResonance
    suspend fun betweenPlaces(baseUrl: String, request: BetweenPlacesRequest): BetweenPlaces
    suspend fun relationship(baseUrl: String, request: RelationshipRequest): RelationshipField
    suspend fun generateReport(baseUrl: String, request: ReportRequest): ReportJob
    suspend fun job(baseUrl: String, jobId: String): ReportJob
    suspend fun report(baseUrl: String, reportId: String): GeneratedReport
}
