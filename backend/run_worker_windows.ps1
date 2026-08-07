param(
    [int]$Port = 8001,
    [string]$NodeName = 'RTX3070TI-WORKER'
)

$ErrorActionPreference = 'Stop'
$env:LMN_NODE_NAME = $NodeName
$env:LMN_NODE_ROLE = 'gpu-worker'
$env:LMN_WORKERS = ''

if (-not (Test-Path '.venv')) {
    python -m venv .venv
}

$python = Join-Path $PWD '.venv\Scripts\python.exe'
$pip = Join-Path $PWD '.venv\Scripts\pip.exe'
& $python -m pip install --upgrade pip
& $pip install -r requirements.txt

Write-Host "Starting $NodeName on port $Port" -ForegroundColor Cyan
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv,noheader
}

& $python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
