@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Installation

if not exist "%~dp0LMNotebook_INSTALL.cmd" (
  echo [ERREUR] LMNotebook_INSTALL.cmd introuvable dans ce dossier.
  pause
  exit /b 1
)

call "%~dp0LMNotebook_INSTALL.cmd"
exit /b %errorlevel%
