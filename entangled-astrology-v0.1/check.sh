#!/usr/bin/env sh
set -eu
./gradlew --version
./gradlew test lintDebug assembleDebug
