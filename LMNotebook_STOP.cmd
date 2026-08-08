@echo off
setlocal EnableExtensions
title LMNotebook Stop
set "ROOT=%~dp0"
set "PY=%~dp0backend\.venv\Scripts\python.exe"

echo.
echo Arret de LMNotebook...
if exist "%PY%" if exist "%ROOT%tools\runtime_manager.py" (
  "%PY%" "%ROOT%tools\runtime_manager.py" stop
)

rem Also clean any visible legacy terminals left by the early launcher versions.
taskkill /FI "WINDOWTITLE eq LMNotebook V2 API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LMNotebook Frontend*" /T /F >nul 2>&1

echo [OK] LMNotebook est arrete.
timeout /t 2 /nobreak >nul
endlocal
