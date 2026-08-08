$ErrorActionPreference = 'Stop'

Write-Host '=== LMNotebook Deep Audio V2 ===' -ForegroundColor Cyan

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    throw 'Python is not available in PATH.'
}
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    throw 'FFmpeg is not available in PATH. Install FFmpeg first and reopen PowerShell.'
}
if (-not (Get-Command ffprobe -ErrorAction SilentlyContinue)) {
    throw 'ffprobe is not available in PATH.'
}

if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host 'NVIDIA GPU detected:' -ForegroundColor Green
    nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
} else {
    Write-Warning 'nvidia-smi not found. V2-A works on CPU, but GPU layers will stay disabled.'
}

if (-not (Test-Path '.venv')) {
    Write-Host 'Creating virtual environment...'
    python -m venv .venv
}

$python = Join-Path $PWD '.venv\Scripts\python.exe'
$pip = Join-Path $PWD '.venv\Scripts\pip.exe'

& $python -m pip install --upgrade pip
& $pip install -r requirements.txt

if (Test-Path '.env') {
    Get-Content '.env' | ForEach-Object {
        if ($_ -match '^\s*#' -or $_ -notmatch '=') { return }
        $name, $value = $_ -split '=', 2
        [Environment]::SetEnvironmentVariable($name.Trim(), $value.Trim(), 'Process')
    }
}

Write-Host ''
Write-Host 'API: http://127.0.0.1:8000' -ForegroundColor Green
Write-Host 'Docs: http://127.0.0.1:8000/docs' -ForegroundColor Green
Write-Host 'LAN : http://<THIS-PC-IP>:8000' -ForegroundColor Yellow
Write-Host ''

& $python -m uvicorn app.entrypoint:app --host 0.0.0.0 --port 8000 --reload
