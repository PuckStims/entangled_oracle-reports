# Build Fix Walkthrough

I have applied several changes to address the build failure and the memory crashes.

## Changes Made

### 1. Memory Optimization
I updated [gradle.properties](file:///C:/entangled_oracle/entangled-astrology-v0.1/gradle.properties) to reduce the memory footprint of the build process:
- Reduced `org.gradle.jvmargs` to `-Xmx1g`.
- Disabled `org.gradle.parallel` and `org.gradle.tooling.parallel`.
> [!NOTE]
> These changes are necessary because the system is extremely memory-constrained (5GB total RAM). Reducing these values helps prevent the JVM from crashing when it tries to allocate memory that isn't available.

### 2. Environment Conflict Resolution
The build was failing with an `AndroidLocationsException` because both `ANDROID_PREFS_ROOT` and `ANDROID_USER_HOME` are set in your environment.

> [!IMPORTANT]
> **Action Required**: You must manually unset the `ANDROID_PREFS_ROOT` environment variable in Windows to permanently fix this conflict.
> 1. Open **Start Menu**, search for "Environment Variables".
> 2. Select "Edit the system environment variables".
> 3. Click **Environment Variables**.
> 4. In "User variables", find `ANDROID_PREFS_ROOT` and click **Delete**.
> 5. Restart Android Studio.

## Verification Results
- I verified that unsetting the variable in a local shell allows the configuration to succeed.
- The full build is still struggling with memory on this specific environment, but the configuration error is resolved by the manual step above.

render_diffs(file:///C:/entangled_oracle/entangled-astrology-v0.1/gradle.properties)
