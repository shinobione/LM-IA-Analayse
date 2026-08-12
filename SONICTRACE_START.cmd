@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Demarrage

rem Pin the expected runtime identity so a stale machine-level LMN_VERSION cannot mask the deployed engine.
set "LMN_VERSION=2.0.3-alpha"

if not exist "%~dp0LMNotebook_START.cmd" (
  echo [ERREUR] LMNotebook_START.cmd introuvable dans ce dossier.
  pause
  exit /b 1
)

call "%~dp0LMNotebook_START.cmd"
exit /b %errorlevel%
