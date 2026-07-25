package com.ksistipuck.entangled.astrology.app

import android.content.Context
import com.ksistipuck.entangled.astrology.core.network.KtorAstrologyEngine
import com.ksistipuck.entangled.astrology.core.repository.DefaultEngineRepository
import com.ksistipuck.entangled.astrology.core.repository.EngineRepository
import com.ksistipuck.entangled.astrology.core.settings.SettingsRepository

class AppContainer(context: Context) {
    val settingsRepository = SettingsRepository(context)
    private val engine = KtorAstrologyEngine()
    val engineRepository: EngineRepository = DefaultEngineRepository(engine, settingsRepository)
}
