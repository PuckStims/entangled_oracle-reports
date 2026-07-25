package com.ksistipuck.entangled.astrology

import android.app.Application
import com.ksistipuck.entangled.astrology.app.AppContainer

class EntangledApplication : Application() {
    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
    }
}
