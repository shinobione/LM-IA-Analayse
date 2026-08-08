$ErrorActionPreference = 'SilentlyContinue'

$Root = Split-Path -Parent $PSScriptRoot
$RuntimeFile = Join-Path $Root '.lmn-runtime.json'

Write-Host ''
Write-Host '=== LMNotebook STOP ===' -ForegroundColor Cyan

if (-not (Test-Path $RuntimeFile)) {
    Write-Host 'Aucune session LMNotebook enregistree.' -ForegroundColor Yellow
    exit 0
}

try {
    $runtime = Get-Content $RuntimeFile -Raw | ConvertFrom-Json
    $pids = @($runtime.backend_pid, $runtime.frontend_pid) | Where-Object { $_ }

    foreach ($pidValue in $pids) {
        $proc = Get-Process -Id ([int]$pidValue) -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Arret du processus $pidValue..." -ForegroundColor DarkGray
            & taskkill.exe /PID $pidValue /T /F | Out-Null
        }
    }

    Remove-Item $RuntimeFile -Force -ErrorAction SilentlyContinue
    Write-Host '[OK] LMNotebook est arrete.' -ForegroundColor Green
} catch {
    Write-Host "Impossible de terminer proprement : $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host 'Tu peux simplement fermer les deux fenetres LMNotebook restantes.' -ForegroundColor DarkGray
}
