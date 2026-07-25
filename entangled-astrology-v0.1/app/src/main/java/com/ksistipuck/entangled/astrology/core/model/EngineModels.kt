package com.ksistipuck.entangled.astrology.core.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
enum class BirthTimeConfidence { EXACT_RECORD, EXACT_RECALLED, APPROXIMATE, UNKNOWN }

@Serializable
data class GeoPoint(val latitude: Double, val longitude: Double)

@Serializable
data class BirthProfile(
    val id: String,
    val displayName: String,
    val localDate: String,
    val localTime: String? = null,
    val timeZoneId: String,
    val locationName: String,
    val coordinates: GeoPoint? = null,
    val birthTimeConfidence: BirthTimeConfidence,
)

@Serializable
data class EngineHealth(
    val status: String,
    val checkedAt: String,
    val message: String? = null,
)

@Serializable
data class EngineIdentity(
    val engine: String,
    val engineVersion: String,
    val schemaVersion: String,
    val ephemeris: String? = null,
    val buildId: String? = null,
)

@Serializable
data class EngineCapabilities(
    val supportedTechniques: List<String>,
    val supportedReports: List<String>,
    val supportedHouseSystems: List<String> = emptyList(),
    val supportsRelationships: Boolean = false,
    val supportsPlaceResonance: Boolean = false,
    val supportsBetweenPlaces: Boolean = false,
)

@Serializable
data class ProfileValidationRequest(val profile: BirthProfile)

@Serializable
data class ValidationIssue(
    val field: String,
    val severity: String,
    val message: String,
)

@Serializable
data class ProfileValidationResponse(
    val valid: Boolean,
    val normalizedProfile: BirthProfile? = null,
    val issues: List<ValidationIssue> = emptyList(),
)

@Serializable
data class Provenance(
    val engineVersion: String,
    val schemaVersion: String,
    val calculationModules: List<String>,
    val normalizationApplied: Boolean,
    val contentPackIds: List<String> = emptyList(),
    val fallbackTierUsed: String? = null,
    val warnings: List<String> = emptyList(),
)

@Serializable
data class CalculatedEvent(
    val id: String,
    val technique: String,
    val movingBody: String? = null,
    val natalTarget: String,
    val aspect: String? = null,
    val orbDegrees: Double? = null,
    val phase: String,
    val startsAt: String? = null,
    val exactAt: String? = null,
    val endsAt: String? = null,
    val lifeAreas: List<String> = emptyList(),
    val birthTimeSensitive: Boolean,
    val title: String? = null,
    val interpretation: String? = null,
)

@Serializable
data class FieldPattern(
    val id: String,
    val title: String,
    val summary: String,
    val role: String,
    val stage: String,
    val eventIds: List<String>,
    val orientation: List<String> = emptyList(),
)

@Serializable
data class CurrentFieldRequest(
    val profile: BirthProfile,
    val moment: String,
    val window: String = "today",
)

@Serializable
data class CurrentField(
    val fieldId: String,
    val calculatedAt: String,
    val timeZone: String,
    val windowStart: String,
    val windowEnd: String,
    val patterns: List<FieldPattern>,
    val events: List<CalculatedEvent>,
    val provenance: Provenance,
)

@Serializable
data class TimelineRequest(
    val profile: BirthProfile,
    val start: String,
    val end: String,
    val techniques: List<String> = emptyList(),
)

@Serializable
data class TimelineResponse(
    val calculatedAt: String,
    val timeZone: String,
    val events: List<CalculatedEvent>,
    val provenance: Provenance,
)

@Serializable
data class ChartPlacement(
    val body: String,
    val sign: String,
    val degree: Double,
    val house: Int? = null,
    val retrograde: Boolean = false,
)

@Serializable
data class ChartAspect(
    val pointA: String,
    val aspect: String,
    val pointB: String,
    val orbDegrees: Double,
)

@Serializable
data class NatalChartRequest(val profile: BirthProfile, val houseSystem: String? = null)

@Serializable
data class NatalChart(
    val calculatedAt: String,
    val timeZone: String,
    val zodiac: String,
    val houseSystem: String,
    val placements: List<ChartPlacement>,
    val aspects: List<ChartAspect>,
    val provenance: Provenance,
)

@Serializable
data class PlaceInput(
    val name: String,
    val coordinates: GeoPoint,
    val timeZoneId: String,
)

@Serializable
data class PlaceResonanceRequest(val profile: BirthProfile, val place: PlaceInput)

@Serializable
data class PlaceLine(
    val planet: String,
    val angle: String,
    val distanceKm: Double,
    val direction: String? = null,
    val birthTimeSensitive: Boolean,
)

@Serializable
data class PlaceResonance(
    val calculatedAt: String,
    val place: PlaceInput,
    val headline: String,
    val summary: String,
    val nearestLines: List<PlaceLine>,
    val themes: List<FieldPattern>,
    val provenance: Provenance,
)

@Serializable
data class BetweenPlacesRequest(val profile: BirthProfile, val places: List<PlaceInput>)

@Serializable
data class PlaceComparison(
    val place: PlaceInput,
    val summary: String,
    val categoryScores: Map<String, Double> = emptyMap(),
)

@Serializable
data class BetweenPlaces(
    val calculatedAt: String,
    val comparisons: List<PlaceComparison>,
    val provenance: Provenance,
)

@Serializable
data class RelationshipRequest(
    val primaryProfile: BirthProfile,
    val secondaryProfile: BirthProfile,
    val relationshipType: String,
)

@Serializable
data class RelationshipField(
    val calculatedAt: String,
    val headline: String,
    val summary: String,
    val patterns: List<FieldPattern>,
    val events: List<CalculatedEvent>,
    val provenance: Provenance,
)

@Serializable
data class ReportRequest(
    val profile: BirthProfile,
    val reportType: String,
    val parameters: Map<String, String> = emptyMap(),
)

@Serializable
data class ReportJob(
    val jobId: String,
    val status: String,
    val submittedAt: String,
    val reportId: String? = null,
    val error: String? = null,
)

@Serializable
data class GeneratedReport(
    val reportId: String,
    val reportType: String,
    val title: String,
    val generatedAt: String,
    val mimeType: String,
    val downloadUrl: String? = null,
    val content: String? = null,
    val provenance: Provenance,
)

@Serializable
data class ApiError(
    val code: String,
    val message: String,
    val details: Map<String, String> = emptyMap(),
)
