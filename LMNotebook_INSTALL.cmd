@echo off
setlocal EnableExtensions
title LMNotebook Installer
set "TARGET=%USERPROFILE%\Documents\LMNotebook-Neural-Audio"
set "REPO=https://github.com/shinobione/LM-IA-Analayse.git"

echo.
echo ============================================================
echo  LMNotebook Neural Audio Analyzer - INSTALLATION AUTOMATIQUE
echo ============================================================
echo.

if exist "%TARGET%\LMNotebook_START.cmd" (
  echo [OK] LMNotebook est deja installe.
  call "%TARGET%\LMNotebook_START.cmd"
  exit /b %errorlevel%
)

where git.exe >nul 2>&1
if errorlevel 1 (
  echo [..] Git manque. Tentative d'installation automatique...
  where winget.exe >nul 2>&1
  if errorlevel 1 goto :nogit
  winget install --id Git.Git --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  set "PATH=%PATH%;C:\Program Files\Git\cmd;%LOCALAPPDATA%\Microsoft\WinGet\Links"
)

where git.exe >nul 2>&1
if errorlevel 1 (
  if exist "C:\Program Files\Git\cmd\git.exe" set "GIT=C:\Program Files\Git\cmd\git.exe"
) else (
  set "GIT=git.exe"
)

if not defined GIT goto :nogit

echo [..] Telechargement du projet...
if not exist "%USERPROFILE%\Documents" mkdir "%USERPROFILE%\Documents"
"%GIT%" clone "%REPO%" "%TARGET%"
if errorlevel 1 goto :fail

echo [OK] Projet installe dans :
echo      %TARGET%
echo.
call "%TARGET%\LMNotebook_START.cmd"
exit /b %errorlevel%

:nogit
echo.
echo [ERREUR] Windows n'a pas pu installer Git automatiquement.
echo Envoie-moi simplement un screenshot de cette fenetre : je te guiderai sans commandes compliquees.
pause
exit /b 1

:fail
echo.
echo [ERREUR] Le telechargement du projet a echoue.
echo Envoie-moi un screenshot de cette fenetre.
pause
exit /b 1
