@echo off
setlocal EnableExtensions

if /I "%~1"=="--run" goto :run

set "ROOT=%~dp0"
set "TMPFILE=%TEMP%\SONICTRACE_RESCUE_UPDATE_%RANDOM%_%RANDOM%.cmd"
copy /Y "%~f0" "%TMPFILE%" >nul
if errorlevel 1 (
  echo [ERREUR] Impossible de creer le lanceur temporaire de secours.
  pause
  exit /b 1
)
call "%TMPFILE%" --run "%ROOT%"
set "RC=%errorlevel%"
del /q "%TMPFILE%" >nul 2>&1
exit /b %RC%

:run
set "ROOT=%~2"
cd /d "%ROOT%"
title SonicTrace - Rescue Update + Start
set "GIT="

echo.
echo ============================================================
echo  SONICTRACE - RESCUE UPDATE + START
echo ============================================================
echo.

if not exist "%ROOT%.git" (
  echo [ERREUR] Dossier .git introuvable : %ROOT%
  goto :fail
)

call :resolve_git
if not defined GIT (
  echo [ERREUR] Git introuvable.
  goto :fail
)

echo [1/5] Sauvegarde automatique des modifications locales...
for /f "delims=" %%I in ('"%GIT%" status --porcelain') do set "DIRTY=1"
if defined DIRTY (
  "%GIT%" stash push --include-untracked -m "SonicTrace rescue backup before sync"
  if errorlevel 1 goto :fail
  echo [OK] Sauvegarde creee dans le stash Git.
) else (
  echo [OK] Dossier de travail deja propre.
)

echo [2/5] Recuperation de origin/main...
"%GIT%" fetch origin main
if errorlevel 1 goto :fail

echo [3/5] Synchronisation locale sur main...
"%GIT%" checkout main
if errorlevel 1 goto :fail
"%GIT%" reset --hard origin/main
if errorlevel 1 goto :fail

echo [4/5] Version installee :
"%GIT%" --no-pager log -1 --oneline

echo [5/5] Demarrage de SonicTrace...
if not exist "%ROOT%SONICTRACE_START.cmd" (
  echo [ERREUR] SONICTRACE_START.cmd introuvable apres synchronisation.
  goto :fail
)
call "%ROOT%SONICTRACE_START.cmd"
exit /b %errorlevel%

:resolve_git
for /f "delims=" %%I in ('where git.exe 2^>nul') do if not defined GIT set "GIT=%%I"
if not defined GIT if exist "%ProgramFiles%\Git\cmd\git.exe" set "GIT=%ProgramFiles%\Git\cmd\git.exe"
if not defined GIT if exist "%ProgramFiles%\Git\bin\git.exe" set "GIT=%ProgramFiles%\Git\bin\git.exe"
if not defined GIT if exist "%LOCALAPPDATA%\Programs\Git\cmd\git.exe" set "GIT=%LOCALAPPDATA%\Programs\Git\cmd\git.exe"
exit /b 0

:fail
echo.
echo [ERREUR] Rescue interrompu. Rien n'a ete restaure par-dessus tes fichiers.
echo Si une sauvegarde a ete creee, elle est visible avec : git stash list
pause
exit /b 1
