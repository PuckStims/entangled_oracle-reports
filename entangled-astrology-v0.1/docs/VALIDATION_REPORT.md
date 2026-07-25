# Repository validation report

Validation was performed during repository assembly on July 18, 2026.

## Passed

- All Android XML resources parse successfully.
- `gradle/libs.versions.toml` parses successfully.
- `openapi/entangled-oracle-v1.yaml` parses successfully and contains 13 API paths and 32 schemas.
- Unix shell scripts pass `bash -n` syntax validation.
- The bootstrap wrapper JAR contains the required `org.gradle.wrapper.GradleWrapperMain` entry point.
- The bootstrap wrapper passed an offline smoke test using a local synthetic distribution, including SHA-256 verification and argument forwarding.
- Pure Kotlin engine models and `EngineResponseValidator` compile under an isolated compiler check with serialization annotation stubs.
- A parser pass across all Kotlin sources found no Kotlin syntax errors.
- A repository scan found no runtime mock charts, transits, readings, scores, or successful fake engine implementations.

## Not executed in the assembly environment

A full `assembleDebug`, Android lint run, emulator launch, and Compose UI test were not possible because the assembly container did not include an Android SDK or cached Android/Compose dependencies. Run the following in Android Studio or a configured CI runner before treating the repository as release-ready:

```bash
./gradlew test lintDebug assembleDebug
```

The project deliberately remains v0.1 integration scaffolding until the real Entangled Oracle engine adapter is built and parity-tested.
