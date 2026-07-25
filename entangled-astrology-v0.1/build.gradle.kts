buildscript {
    dependencies {
        // AGP 9 uses built-in Kotlin. Pinning KGP keeps the Compose and serialization
        // compiler plugins on the same Kotlin release.
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.4.10")
    }
}

plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.compose.compiler) apply false
    alias(libs.plugins.kotlin.serialization) apply false
}
