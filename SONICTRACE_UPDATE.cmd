@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Mise a jour sure

set "ROOT=%~dp0"
set "GIT="
set "DIRTY="
set "BACKUP_CREATED=0"

echo.
echo ============================================================
echo  SONICTRACE - MISE A JOUR SURE
echo ============================================================
echo.

if not exist "%ROOT%.git" (
  echo [ERREUR] Ce fichier doit etre lance depuis le dossier SonicTrace clone avec Git.
  echo Dossier actuel : %ROOT%
  goto :fail
)

call :resolve_git
if not defined GIT (
  echo [1/5] Git absent. Installation automatique via winget...
  where winget.exe >nul 2>&1
  if errorlevel 1 (
    echo [ERREUR] Git n'est pas installe et winget est indisponible.
    goto :fail
  )
  winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 goto :fail
  call :resolve_git
) else (
  echo [1/5] Git trouve : %GIT%
)
if not defined GIT goto :fail

echo [2/5] Verification du depot...
"%GIT%" remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] Aucun remote Git nomme origin n'est configure.
  goto :fail
)

for /f "delims=" %%I in ('"%GIT%" status --porcelain') do set "DIRTY=1"
if defined DIRTY (
  echo.
  echo [INFO] Modifications locales detectees.
  echo Elles vont etre sauvegardees automatiquement dans un stash Git.
  echo Aucun fichier local ne sera perdu.
  echo.
  echo [3/5] Sauvegarde de secours des fichiers locaux...
  "%GIT%" stash push --include-untracked -m "SonicTrace auto-backup before update"
  if errorlevel 1 (
    echo [ERREUR] Impossible de sauvegarder les changements locaux.
    echo Mise a jour annulee pour proteger tes fichiers.
    goto :fail
  )
  set "BACKUP_CREATED=1"
) else (
  echo [3/5] Aucun changement local a sauvegarder.
)

echo [4/5] Recuperation de la derniere version de main...
"%GIT%" fetch origin main
if errorlevel 1 goto :fail

"%GIT%" checkout main
if errorlevel 1 goto :fail

"%GIT%" pull --ff-only origin main
if errorlevel 1 (
  echo.
  echo [ERREUR] Git a refuse la mise a jour automatique.
  if "%BACKUP_CREATED%"=="1" echo Tes anciens fichiers restent proteges dans le stash Git.
  goto :fail
)

echo [5/5] Version installee :
"%GIT%" --no-pager log -1 --oneline
echo.
echo [OK] SonicTrace est a jour.
if "%BACKUP_CREATED%"=="1" (
  echo [OK] Tes anciens fichiers locaux sont conserves dans :
  "%GIT%" stash list -1
  echo Pour les restaurer manuellement plus tard : git stash pop
)
echo.
if /I "%SONICTRACE_NO_PAUSE%"=="1" exit /b 0
pause
exit /b 0

:resolve_git
set "GIT="
for /f "delims=" %%I in ('where git.exe 2^>nul') do if not defined GIT set "GIT=%%I"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%ProgramFiles%\Git\bin\git.exe" set "GIT=%ProgramFiles%\Git\bin\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
exit /b 0

:fail
echo.
echo La mise a jour n'a pas ete appliquee.
if /I "%SONICTRACE_NO_PAUSE%"=="1" exit /b 1
pause
exit /b 1
