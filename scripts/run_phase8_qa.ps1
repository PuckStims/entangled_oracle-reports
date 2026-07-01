$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
Push-Location $repoRoot

try {
    python -m unittest discover -s .\tests -p "test_*.py"
    python .\scripts\generate_review_pack.py
}
finally {
    Pop-Location
}
