@echo off
setlocal EnableExtensions
title LMNotebook RESCUE
set "TARGET=%USERPROFILE%\Documents\LMNotebook-Neural-Audio"

echo.
echo ============================================================
echo  LMNotebook Neural Audio Analyzer - RESCUE
echo ============================================================
echo.

if not exist "%TARGET%\LMNotebook_START.cmd" (
  echo [ERREUR] Installation LMNotebook introuvable :
  echo %TARGET%
  pause
  exit /b 1
)

set "GIT="
where git.exe >nul 2>&1 && set "GIT=git.exe"
if not defined GIT if exist "C:\Program Files\Git\cmd\git.exe" set "GIT=C:\Program Files\Git\cmd\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"

echo [1/3] Recuperation de la derniere correction...
if defined GIT (
  "%GIT%" -C "%TARGET%" pull --ff-only
  if errorlevel 1 goto :updatefail
) else (
  echo [INFO] Git introuvable dans ce terminal. Telechargement direct des fichiers critiques...
  powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/shinobione/LM-IA-Analayse/main/LMNotebook_START.cmd' -OutFile '%TARGET%\LMNotebook_START.cmd'; Invoke-WebRequest -UseBasicParsing 'https://raw.githubusercontent.com/shinobione/LM-IA-Analayse/main/tools/bootstrap_windows.ps1' -OutFile '%TARGET%\tools\bootstrap_windows.ps1'"
  if errorlevel 1 goto :updatefail
)

echo.
echo [2/3] Creation securisee de l'environnement Python...
set "PY="
set "PYLAUNCHER="
where python.exe >nul 2>&1 && set "PY=python.exe"
if not defined PY if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not defined PY if exist "C:\Program Files\Python312\python.exe" set "PY=C:\Program Files\Python312\python.exe"
if not defined PY where py.exe >nul 2>&1 && set "PYLAUNCHER=1"

if exist "%TARGET%\backend\.venv" if not exist "%TARGET%\backend\.venv\Scripts\python.exe" rmdir /s /q "%TARGET%\backend\.venv"

if not exist "%TARGET%\backend\.venv\Scripts\python.exe" (
  if defined PY (
    "%PY%" -m venv "%TARGET%\backend\.venv"
  ) else if defined PYLAUNCHER (
    py.exe -3.12 -m venv "%TARGET%\backend\.venv"
    if errorlevel 1 py.exe -3 -m venv "%TARGET%\backend\.venv"
  ) else (
    echo [ERREUR] Python 3.12 est installe mais introuvable depuis cette session Windows.
    echo Relance simplement ce Rescue une fois. Si cela persiste, envoie-moi le screenshot.
    pause
    exit /b 1
  )
)

if not exist "%TARGET%\backend\.venv\Scripts\python.exe" (
  echo [ERREUR] L'environnement Python n'a pas ete cree.
  pause
  exit /b 1
)

echo [OK] Environnement Python pret.
echo.
echo [3/3] Lancement de LMNotebook...
call "%TARGET%\LMNotebook_START.cmd"
exit /b %errorlevel%

:updatefail
echo.
echo [ERREUR] Impossible de recuperer la correction.
echo Envoie-moi un screenshot de cette fenetre.
pause
exit /b 1
