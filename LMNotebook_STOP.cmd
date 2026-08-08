@echo off
setlocal
cd /d "%~dp0"
title LMNotebook Stop
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\stop_windows.ps1"
endlocal
