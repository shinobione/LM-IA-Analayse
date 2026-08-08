@echo off
setlocal
cd /d "%~dp0"
title LMNotebook Launcher
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\bootstrap_windows.ps1"
if errorlevel 1 (
  echo.
  echo [LMNotebook] Le lancement a rencontre un probleme.
  echo Le diagnostic est affiche ci-dessus et enregistre dans le dossier logs.
  pause
)
endlocal
