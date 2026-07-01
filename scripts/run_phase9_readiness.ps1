$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    python -m unittest discover -s .\tests -p "test_*.py"
    python .\scripts\generate_review_pack.py
    python .\scripts\build_phase9_baseline.py
}
finally {
    Pop-Location
}
