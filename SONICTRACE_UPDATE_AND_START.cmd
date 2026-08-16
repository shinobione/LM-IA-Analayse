@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Update + Start

set "SONICTRACE_NO_PAUSE=1"
call "%~dp0SONICTRACE_UPDATE.cmd"
if errorlevel 1 (
  echo.
  echo [ERREUR] Demarrage annule car la mise a jour a echoue.
  pause
  exit /b 1
)

rem Engine updates must never reuse a stale schema-compatible Python process.
rem Stop tracked PIDs AND any orphan listener still owning SonicTrace fixed ports.
if exist "%~dp0LMNotebook_STOP.cmd" (
  call "%~dp0LMNotebook_STOP.cmd"
  if errorlevel 1 (
    echo.
    echo [ERREUR] L'ancien runtime SonicTrace n'a pas pu etre arrete completement.
    echo Ferme les anciennes fenetres SonicTrace puis relance ce fichier.
    pause
    exit /b 1
  )
)

set "SONICTRACE_NO_PAUSE="
call "%~dp0SONICTRACE_START.cmd"
exit /b %errorlevel%
