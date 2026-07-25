package com.ksistipuck.entangled.astrology.app

import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.ksistipuck.entangled.astrology.core.model.*
import com.ksistipuck.entangled.astrology.core.repository.EngineConnectionState
import com.ksistipuck.entangled.astrology.core.settings.AppSettings
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.combine
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneId
import java.util.UUID

sealed interface DataState<out T> {
    data object Idle : DataState<Nothing>
    data object Loading : DataState<Nothing>
    data class Ready<T>(val value: T) : DataState<T>
    data class Error(val message: String) : DataState<Nothing>
}

data class AppUiState(
    val settings: AppSettings? = null,
    val connection: EngineConnectionState = EngineConnectionState.Unconfigured,
    val currentField: DataState<CurrentField> = DataState.Idle,
    val timeline: DataState<TimelineResponse> = DataState.Idle,
    val natalChart: DataState<NatalChart> = DataState.Idle,
    val placeResonance: DataState<PlaceResonance> = DataState.Idle,
)

private data class CalculationStates(
    val currentField: DataState<CurrentField>,
    val timeline: DataState<TimelineResponse>,
    val natalChart: DataState<NatalChart>,
    val placeResonance: DataState<PlaceResonance>,
)

class AppViewModel(private val container: AppContainer) : ViewModel() {
    private val currentField = MutableStateFlow<DataState<CurrentField>>(DataState.Idle)
    private val timeline = MutableStateFlow<DataState<TimelineResponse>>(DataState.Idle)
    private val natalChart = MutableStateFlow<DataState<NatalChart>>(DataState.Idle)
    private val placeResonance = MutableStateFlow<DataState<PlaceResonance>>(DataState.Idle)

    private val foundation = combine(
        container.settingsRepository.settings,
        container.engineRepository.connectionState,
    ) { settings, connection -> settings to connection }

    private val calculationStates = combine(
        currentField,
        timeline,
        natalChart,
        placeResonance,
    ) { field, timelineValue, chart, place ->
        CalculationStates(field, timelineValue, chart, place)
    }

    val uiState: StateFlow<AppUiState> = combine(foundation, calculationStates) { base, calculations ->
        AppUiState(
            settings = base.first,
            connection = base.second,
            currentField = calculations.currentField,
            timeline = calculations.timeline,
            natalChart = calculations.natalChart,
            placeResonance = calculations.placeResonance,
        )
    }.stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), AppUiState())

    fun saveEngineUrl(url: String) = viewModelScope.launch {
        container.settingsRepository.setEngineBaseUrl(url)
    }

    fun saveAndTestEngineUrl(url: String) = viewModelScope.launch {
        container.settingsRepository.setEngineBaseUrl(url)
        container.engineRepository.testConnection()
    }

    fun testConnection() = viewModelScope.launch { container.engineRepository.testConnection() }

    fun saveProfile(profile: BirthProfile) = viewModelScope.launch {
        container.settingsRepository.saveProfile(profile)
        clearCalculatedData()
    }

    fun createProfile(
        name: String,
        date: String,
        time: String,
        location: String,
        timeZone: String,
        confidence: BirthTimeConfidence,
    ): BirthProfile = BirthProfile(
        id = UUID.randomUUID().toString(),
        displayName = name.trim(),
        localDate = date.trim(),
        localTime = time.trim().ifBlank { null },
        timeZoneId = timeZone.trim(),
        locationName = location.trim(),
        birthTimeConfidence = confidence,
    )

    fun loadCurrentField(window: String = "today") = viewModelScope.launch {
        val profile = uiState.value.settings?.profile ?: return@launch
        currentField.value = DataState.Loading
        val result = container.engineRepository.currentField(
            CurrentFieldRequest(profile, Instant.now().toString(), window)
        )
        currentField.value = result.fold({ DataState.Ready(it) }, { DataState.Error(it.message ?: "Calculation failed") })
    }

    fun loadTimeline(days: Long = 7) = viewModelScope.launch {
        val profile = uiState.value.settings?.profile ?: return@launch
        val zone = runCatching { ZoneId.of(profile.timeZoneId) }.getOrDefault(ZoneId.systemDefault())
        val start = LocalDate.now(zone)
        timeline.value = DataState.Loading
        val result = container.engineRepository.timeline(
            TimelineRequest(profile, start.toString(), start.plusDays(days).toString())
        )
        timeline.value = result.fold({ DataState.Ready(it) }, { DataState.Error(it.message ?: "Timeline failed") })
    }

    fun loadNatalChart() = viewModelScope.launch {
        val profile = uiState.value.settings?.profile ?: return@launch
        natalChart.value = DataState.Loading
        val result = container.engineRepository.natalChart(NatalChartRequest(profile))
        natalChart.value = result.fold({ DataState.Ready(it) }, { DataState.Error(it.message ?: "Chart failed") })
    }

    fun loadPlace(place: PlaceInput) = viewModelScope.launch {
        val profile = uiState.value.settings?.profile ?: return@launch
        placeResonance.value = DataState.Loading
        val result = container.engineRepository.placeResonance(PlaceResonanceRequest(profile, place))
        placeResonance.value = result.fold({ DataState.Ready(it) }, { DataState.Error(it.message ?: "Place calculation failed") })
    }

    fun setReducedMotion(value: Boolean) = viewModelScope.launch { container.settingsRepository.setReducedMotion(value) }
    fun setLowStimulation(value: Boolean) = viewModelScope.launch { container.settingsRepository.setLowStimulation(value) }
    fun setHighContrast(value: Boolean) = viewModelScope.launch { container.settingsRepository.setHighContrast(value) }
    fun setTextScale(value: Float) = viewModelScope.launch { container.settingsRepository.setTextScale(value) }

    private fun clearCalculatedData() {
        currentField.value = DataState.Idle
        timeline.value = DataState.Idle
        natalChart.value = DataState.Idle
        placeResonance.value = DataState.Idle
    }

    class Factory(private val container: AppContainer) : ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : ViewModel> create(modelClass: Class<T>): T = AppViewModel(container) as T
    }
}
