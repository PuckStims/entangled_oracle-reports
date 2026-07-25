# Architecture

```text
Jetpack Compose screens
        ↓
AppViewModel / StateFlow
        ↓
EngineRepository
        ↓
AstrologyEngine interface
        ↓
KtorAstrologyEngine
        ↓
Entangled Oracle API adapter
        ↓
Existing Python calculation and report engine
```

## Non-negotiable boundary

The Android application does not calculate planetary positions and does not ask a language model to do so. It renders only validated engine responses.

## State model

Each calculation surface supports:

- unconfigured,
- unavailable,
- idle,
- loading,
- validated success,
- schema/connection error.

There is no demo-success branch in production source code.

## Storage

DataStore currently stores the configured engine URL, one birth profile, and accessibility preferences. A later release can add encrypted storage, multiple profiles, and a Room-backed report index.

## Backend migration freedom

`AstrologyEngine` is deliberately independent of transport. A later implementation can use embedded Python, JNI, a local companion service, or native Kotlin without changing screen contracts.
