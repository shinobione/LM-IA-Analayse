@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Arret

if not exist "%~dp0LMNotebook_STOP.cmd" (
  echo [ERREUR] LMNotebook_STOP.cmd introuvable dans ce dossier.
  pause
  exit /b 1
)

call "%~dp0LMNotebook_STOP.cmd"
exit /b %errorlevel%
