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

rem Build updates can preserve a schema-compatible API process from an older engine.
rem Force a clean managed stop after the pull so the new code is guaranteed to boot.
if exist "%~dp0LMNotebook_STOP.cmd" call "%~dp0LMNotebook_STOP.cmd"

set "SONICTRACE_NO_PAUSE="
call "%~dp0SONICTRACE_START.cmd"
exit /b %errorlevel%
