@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook Launcher

rem ---------------------------------------------------------------------------
rem Resolve a real Python executable from common Windows locations.
rem The virtual environment is created here in CMD before PowerShell starts.
rem ---------------------------------------------------------------------------
set "PY="
set "PYLAUNCHER="
where python.exe >nul 2>&1 && set "PY=python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY if exist "C:\Program Files\Python312\python.exe" set "PY=C:\Program Files\Python312\python.exe"
if not defined PY (
  where py.exe >nul 2>&1 && set "PYLAUNCHER=1"
)

if not exist "%~dp0backend\.venv\Scripts\python.exe" (
  echo [LMNotebook] Preparation de l'environnement Python...
  if exist "%~dp0backend\.venv" rmdir /s /q "%~dp0backend\.venv"

  if defined PY (
    "%PY%" -m venv "%~dp0backend\.venv"
  ) else if defined PYLAUNCHER (
    py.exe -3.12 -m venv "%~dp0backend\.venv"
    if errorlevel 1 py.exe -3 -m venv "%~dp0backend\.venv"
  )

  if exist "%~dp0backend\.venv\Scripts\python.exe" (
    echo [OK] Environnement Python cree.
  ) else (
    echo [INFO] Python n'est pas encore accessible depuis CMD. Le bootstrap va verifier les prerequis.
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
