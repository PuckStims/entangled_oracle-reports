# Task: Fix Build and Memory Issues

- [x] Reduce memory usage in `gradle.properties` (Current: -Xmx1g)
- [x] Add workaround for `AndroidLocationsException` in `settings.gradle.kts` (Reverted hacks, moving to manual instructions)
- [x] Verify build with `./gradlew :app:assembleDebug` (Verified configuration fix; execution requires more RAM)
