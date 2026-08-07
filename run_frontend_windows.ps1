$ErrorActionPreference = 'Stop'

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python is not available in PATH.'
}

Write-Host 'LMNotebook frontend: http://127.0.0.1:8008' -ForegroundColor Cyan
Write-Host 'Use this local URL while the V2 API runs on http://127.0.0.1:8000.' -ForegroundColor DarkGray
python -m http.server 8008 --bind 127.0.0.1
