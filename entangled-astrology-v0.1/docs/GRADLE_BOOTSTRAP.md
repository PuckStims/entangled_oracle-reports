# Gradle bootstrap wrapper

## Why it exists

The repository assembly environment could create and test source files but could not retrieve binary artifacts from Gradle's distribution host. To keep the ZIP directly runnable, the repository includes a minimal Java bootstrap at the standard `org.gradle.wrapper.GradleWrapperMain` entry point.

## Behavior

The bootstrap:

1. Reads `gradle/wrapper/gradle-wrapper.properties`.
2. Downloads the configured distribution when it is not cached.
3. Verifies `distributionSha256Sum` before extraction.
4. Rejects ZIP entries which would escape the destination directory.
5. Starts the extracted Gradle executable and forwards all arguments and exit status.

It does not modify build files or bypass Gradle verification.

## Validation performed

The wrapper was compiled with JDK 17 and smoke-tested against a local synthetic Gradle distribution. The test confirmed property parsing, checksum verification, extraction, executable discovery, argument forwarding, and exit-code propagation.

## Recommended replacement

Once the project can complete a normal Gradle sync, regenerate the official wrapper:

```bash
./gradlew wrapper --gradle-version 9.4.1
```

Commit the regenerated `gradle-wrapper.jar`, scripts, and properties together.
