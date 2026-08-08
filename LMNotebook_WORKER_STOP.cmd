@echo off
setlocal EnableExtensions
title LMNotebook GPU Worker Stop
set "ROOT=%~dp0"
set "PY=%~dp0backend\.venv\Scripts\python.exe"

echo.
echo Arret du worker GPU LMNotebook...
if exist "%PY%" if exist "%ROOT%tools\worker_runtime.py" (
  "%PY%" "%ROOT%tools\worker_runtime.py" stop
) else (
  echo [INFO] Aucun runtime worker gere trouve.
)
echo [OK] Termine.
timeout /t 2 /nobreak >nul
endlocal
