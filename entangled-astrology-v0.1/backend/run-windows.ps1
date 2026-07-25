$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$defaultEngineRoot = (Resolve-Path -LiteralPath (Join-Path $scriptRoot "..\..")).Path
if (-not $env:EO_ENGINE_ROOT) {
    $env:EO_ENGINE_ROOT = $defaultEngineRoot
}

$hostName = if ($env:EO_API_HOST) { $env:EO_API_HOST } else { "127.0.0.1" }
$port = if ($env:EO_API_PORT) { $env:EO_API_PORT } else { "8000" }
$venvPython = Join-Path $env:EO_ENGINE_ROOT ".venv\Scripts\python.exe"
$python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

& $python -m uvicorn entangled_mobile_backend.main:app --app-dir $scriptRoot --host $hostName --port $port
