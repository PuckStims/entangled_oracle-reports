@echo off
setlocal
call gradlew.bat --version || exit /b 1
call gradlew.bat test lintDebug assembleDebug || exit /b 1
echo.
echo Entangled Astrology checks completed successfully.
