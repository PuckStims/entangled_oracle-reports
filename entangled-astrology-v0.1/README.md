# Entangled Astrology v0.1

Native Android scaffold for **Entangled Astrology**, one application in the wider **Entangled** ecosystem. The frontend is intentionally incapable of inventing astrology content. Calculation surfaces either call the real Entangled Oracle engine or remain visibly unavailable.

## What is real in this repository

- Kotlin + Jetpack Compose Android application
- Mobile-first five-tab navigation: Today, Timeline, Chart, Places, Library
- Local birth-profile and accessibility storage through DataStore
- Typed `AstrologyEngine` boundary
- Functional Ktor API client
- Strict Kotlin serialization
- Configurable backend URL and connection diagnostics
- Current Field, timeline, natal chart, Place Resonance, report-job contracts
- Calculation provenance and supporting-event requirements
- Response validation that rejects unsupported field synthesis
- Entangled ecosystem switcher
- FastAPI bridge over the existing Entangled Oracle engine
- Real natal chart, Current Field, timeline, profile validation, and HTML report-generation endpoints
- No runtime sample charts, transits, interpretations, or scores

## What is deliberately not fabricated

The repository contains no successful fake API implementation. Structured Place Resonance, Between Places, and Relationships are still gated until their source-to-output mappings are proven.

## Open in Android Studio

Requirements:

- Android Studio compatible with AGP 9.2+
- JDK 17+
- Android SDK 37 and Build Tools 36.0.0+

Open the repository root and allow Gradle sync. From a terminal:

```bash
./gradlew test lintDebug assembleDebug
```

Windows:

```bat
gradlew.bat test lintDebug assembleDebug
```

On this 5 GB RAM Windows machine, large Android builds may need a smaller Gradle memory profile:

```powershell
$env:GRADLE_OPTS='-Xmx1536m -XX:MaxMetaspaceSize=512m -Dfile.encoding=UTF-8'
.\gradlew.bat --no-daemon --max-workers=1 assembleDebug
```

## Connect a development backend

Windows backend start:

```powershell
cd C:\entangled_oracle\entangled-astrology-v0.1\backend
$env:EO_ENGINE_ROOT = "C:\entangled_oracle"
$env:EO_API_HOST = "0.0.0.0"
$env:EO_API_PORT = "8000"
.\run-windows.ps1
```

In Android, open Settings > Engine & accessibility.

For an emulator, use:

```text
http://10.0.2.2:8000
```

For a real phone on the same Wi-Fi, use:

```text
http://YOUR_COMPUTER_IPV4:8000
```

Then tap **Save and test**, create a birth profile, and request a chart, Current Field, or timeline calculation.

For a physical Android device, allow Python through Windows Firewall on private networks. Cleartext HTTP is enabled for development only and must be restricted before release.

## Handoff to Codex

Give Codex:

- this repository,
- the Entangled Oracle engine repository or selected files,
- the current CLI command,
- a known-good raw output,
- a known-good report,
- ephemeris setup and environment requirements.

Then use `docs/CODEX_BACKEND_BUILD_PROMPT.md`.

## Version posture

This is v0.1: an integration-oriented frontend and local development backend, not a claim that the consumer release is finished.

## Gradle bootstrap note

This ZIP includes a small audited bootstrap `gradle-wrapper.jar` because the build environment used to assemble the repository could not download binary wrapper artifacts directly. It reads `gradle-wrapper.properties`, verifies the configured Gradle distribution SHA-256, extracts it safely, and launches Gradle. Its local offline smoke test is documented in `docs/GRADLE_BOOTSTRAP.md`.

After the first successful sync, the integration developer may replace it with Gradle's standard generated wrapper by running:

```bash
./gradlew wrapper --gradle-version 9.4.1
```
