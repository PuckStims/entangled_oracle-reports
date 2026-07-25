package com.ksistipuck.entangled.astrology.core.network

import com.ksistipuck.entangled.astrology.core.model.*
import io.ktor.client.HttpClient
import io.ktor.client.call.body
import io.ktor.client.engine.okhttp.OkHttp
import io.ktor.client.plugins.HttpRequestTimeoutException
import io.ktor.client.plugins.contentnegotiation.ContentNegotiation
import io.ktor.client.plugins.logging.LogLevel
import io.ktor.client.plugins.logging.Logger
import io.ktor.client.plugins.logging.Logging
import io.ktor.client.plugins.timeout
import io.ktor.client.request.get
import io.ktor.client.request.post
import io.ktor.client.request.setBody
import io.ktor.http.ContentType
import io.ktor.http.contentType
import io.ktor.http.isSuccess
import io.ktor.client.statement.bodyAsText
import io.ktor.serialization.kotlinx.json.json
import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import java.io.IOException

class EngineException(message: String, cause: Throwable? = null) : RuntimeException(message, cause)

class KtorAstrologyEngine(
    private val client: HttpClient = defaultClient(),
) : AstrologyEngine {

    override suspend fun health(baseUrl: String): EngineHealth = get(baseUrl, "/v1/health")
    override suspend fun identity(baseUrl: String): EngineIdentity = get(baseUrl, "/v1/engine/identity")
    override suspend fun capabilities(baseUrl: String): EngineCapabilities = get(baseUrl, "/v1/capabilities")
    override suspend fun validateProfile(baseUrl: String, request: ProfileValidationRequest): ProfileValidationResponse = post(baseUrl, "/v1/profiles/validate", request)
    override suspend fun natalChart(baseUrl: String, request: NatalChartRequest): NatalChart = post(baseUrl, "/v1/charts/natal", request)
    override suspend fun currentField(baseUrl: String, request: CurrentFieldRequest): CurrentField = post(baseUrl, "/v1/fields/current", request)
    override suspend fun timeline(baseUrl: String, request: TimelineRequest): TimelineResponse = post(baseUrl, "/v1/timelines/calculate", request)
    override suspend fun placeResonance(baseUrl: String, request: PlaceResonanceRequest): PlaceResonance = post(baseUrl, "/v1/places/resonance", request)
    override suspend fun betweenPlaces(baseUrl: String, request: BetweenPlacesRequest): BetweenPlaces = post(baseUrl, "/v1/places/compare", request)
    override suspend fun relationship(baseUrl: String, request: RelationshipRequest): RelationshipField = post(baseUrl, "/v1/relationships/calculate", request)
    override suspend fun generateReport(baseUrl: String, request: ReportRequest): ReportJob = post(baseUrl, "/v1/reports/generate", request)
    override suspend fun job(baseUrl: String, jobId: String): ReportJob = get(baseUrl, "/v1/jobs/$jobId")
    override suspend fun report(baseUrl: String, reportId: String): GeneratedReport = get(baseUrl, "/v1/reports/$reportId")

    private suspend inline fun <reified T> get(baseUrl: String, path: String): T = translateErrors {
        val response = client.get(url(baseUrl, path)) { timeout { requestTimeoutMillis = 20_000 } }
        if (!response.status.isSuccess()) throw EngineException("Engine returned HTTP ${response.status.value} for $path: ${response.bodyAsText().take(500)}")
        response.body()
    }

    private suspend inline fun <reified Request : Any, reified Response> post(
        baseUrl: String,
        path: String,
        body: Request,
    ): Response = translateErrors {
        val response = client.post(url(baseUrl, path)) {
            contentType(ContentType.Application.Json)
            setBody(body)
            timeout { requestTimeoutMillis = requestTimeoutMillis(path) }
        }
        if (!response.status.isSuccess()) throw EngineException("Engine returned HTTP ${response.status.value} for $path: ${response.bodyAsText().take(500)}")
        response.body()
    }

    private suspend inline fun <T> translateErrors(crossinline block: suspend () -> T): T = try {
        block()
    } catch (error: EngineException) {
        throw error
    } catch (error: HttpRequestTimeoutException) {
        throw EngineException("The engine did not respond before the request timed out.", error)
    } catch (error: SerializationException) {
        throw EngineException("The engine response does not match the Entangled schema.", error)
    } catch (error: IOException) {
        throw EngineException("Could not reach the configured engine.", error)
    }

    private fun url(baseUrl: String, path: String): String = baseUrl.trimEnd('/') + path

    private fun requestTimeoutMillis(path: String): Long = when (path) {
        "/v1/timelines/calculate" -> 180_000
        "/v1/fields/current" -> 120_000
        else -> 60_000
    }

    companion object {
        private fun defaultClient() = HttpClient(OkHttp) {
            expectSuccess = false
            install(ContentNegotiation) {
                json(Json {
                    ignoreUnknownKeys = false
                    explicitNulls = false
                    isLenient = false
                })
            }
            install(Logging) {
                logger = object : Logger {
                    override fun log(message: String) = Unit // Never log birth data by default.
                }
                level = LogLevel.NONE
            }
        }
    }
}
