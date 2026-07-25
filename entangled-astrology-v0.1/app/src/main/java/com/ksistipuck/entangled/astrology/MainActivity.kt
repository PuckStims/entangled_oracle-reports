package com.ksistipuck.entangled.astrology

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.ksistipuck.entangled.astrology.app.EntangledApp

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        val container = (application as EntangledApplication).container
        setContent { EntangledApp(container) }
    }
}
