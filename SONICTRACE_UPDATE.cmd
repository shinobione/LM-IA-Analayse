@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Mise a jour

set "ROOT=%~dp0"
set "GIT="

echo.
echo ============================================================
echo  SONICTRACE - MISE A JOUR
echo ============================================================
echo.

if not exist "%ROOT%.git" (
  echo [ERREUR] Ce fichier doit etre lance depuis le dossier SonicTrace clone avec Git.
  echo Dossier actuel : %ROOT%
  goto :fail
)

call :resolve_git
if not defined GIT (
  echo [1/4] Git absent. Installation automatique via winget...
  where winget.exe >nul 2>&1
  if errorlevel 1 (
    echo [ERREUR] Git n'est pas installe et winget est indisponible.
    goto :fail
  )
  winget install --id Git.Git -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 goto :fail
  call :resolve_git
) else (
  echo [1/4] Git trouve : %GIT%
)
if not defined GIT goto :fail

echo [2/4] Verification du depot...
"%GIT%" remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] Aucun remote Git nomme origin n'est configure.
  goto :fail
)

for /f "delims=" %%I in ('"%GIT%" status --porcelain') do set "DIRTY=1"
if defined DIRTY (
  echo.
  echo [ATTENTION] Des fichiers locaux ont ete modifies.
  echo La mise a jour utilisera uniquement un fast-forward et ne supprimera rien.
  echo Si Git refuse, tes modifications resteront intactes.
  echo.
)

echo [3/4] Recuperation de la derniere version de main...
"%GIT%" fetch origin main
if errorlevel 1 goto :fail

"%GIT%" checkout main
if errorlevel 1 (
  echo [ERREUR] Impossible de basculer sur main. Verifie les modifications locales affichees ci-dessus.
  goto :fail
)

"%GIT%" pull --ff-only origin main
if errorlevel 1 (
  echo.
  echo [ERREUR] Git a refuse la mise a jour automatique.
  echo Rien n'a ete efface. Tes fichiers locaux sont preserves.
  goto :fail
)

echo [4/4] Version installee :
"%GIT%" --no-pager log -1 --oneline
echo.
echo [OK] SonicTrace est a jour.
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
