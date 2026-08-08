@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook Launcher

rem ---------------------------------------------------------------------------
rem Safety net: create the Python virtual environment from CMD, not PowerShell.
rem This avoids the Windows PowerShell argument-binding issue that could open
rem the Python interactive REPL (>>>) instead of running `python -m venv`.
rem ---------------------------------------------------------------------------
if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  where python.exe >nul 2>&1
  if not errorlevel 1 (
    echo [LMNotebook] Preparation de l'environnement Python...
    if exist "%~dp0backend\.venv" rmdir /s /q "%~dp0backend\.venv"
    python.exe -m venv "%~dp0backend\.venv"
    if errorlevel 1 (
      echo [LMNotebook] Le venv n'a pas pu etre cree maintenant. Le bootstrap va tenter de reparer les prerequis.
    ) else (
      echo [OK] Environnement Python cree.
    )
  )
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\bootstrap_windows.ps1"
if errorlevel 1 (
  echo.
  echo [LMNotebook] Le lancement a rencontre un probleme.
  echo Le diagnostic est affiche ci-dessus et enregistre dans le dossier logs.
  pause
)
endlocal
