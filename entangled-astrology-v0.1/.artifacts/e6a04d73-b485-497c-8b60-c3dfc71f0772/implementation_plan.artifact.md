# Fix Build Errors (Environment Conflict and Out of Memory)

The build is failing due to two main reasons:
1. **Environment Variable Conflict**: The Android Gradle Plugin (AGP) detects both `ANDROID_PREFS_ROOT` and `ANDROID_USER_HOME` environment variables, which it considers a conflict.
2. **Out of Memory (JVM Crash)**: The build daemon crashes because it attempts to allocate more memory than is available on the system (5GB total RAM), especially with parallel execution and a 3GB heap.

## User Review Required
> [!IMPORTANT]
> To permanently fix the environment conflict, it is recommended to **unset the `ANDROID_PREFS_ROOT` environment variable** in your system settings. AGP 9.2.1 is particularly strict about this.

> [!NOTE]
> I am reducing the memory allocation for Gradle to improve stability on this system. This may result in slightly slower build times but should prevent the "Out of Memory" crashes.

## Proposed Changes

### Build Configuration

#### [MODIFY] [gradle.properties](file:///C:/entangled_oracle/entangled-astrology-v0.1/gradle.properties)
- Reduce `org.gradle.jvmargs` to `-Xmx2g` (from `3g`).
- Set `org.gradle.parallel=false` to reduce concurrent memory pressure.
- Set `org.gradle.tooling.parallel=false` to reduce memory usage during sync.

#### [MODIFY] [settings.gradle.kts](file:///C:/entangled_oracle/entangled-astrology-v0.1/settings.gradle.kts)
- Add a script block to attempt to clear the conflicting system property if it is passed through to the JVM.

## Verification Plan

### Automated Tests
- Run `./gradlew help` to verify configuration succeeds.
- Run `./gradlew :app:assembleDebug` to verify the full build completes without crashing.

### Manual Verification
- Check the terminal output for any remaining "Several environment variables" warnings or "Out of Memory" errors.
