@echo off
setlocal EnableExtensions
title LMNotebook Stop
echo.
echo Arret de LMNotebook...
taskkill /FI "WINDOWTITLE eq LMNotebook V2 API*" /T /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq LMNotebook Frontend*" /T /F >nul 2>&1
echo [OK] LMNotebook est arrete.
timeout /t 2 /nobreak >nul
endlocal
