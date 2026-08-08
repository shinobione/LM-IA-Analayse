@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook Launcher

set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "VENV=%~dp0backend\.venv"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

echo.
echo ============================================================
echo  LMNotebook Neural Audio Analyzer - SAFE RUNTIME
echo ============================================================
echo.
echo LMNotebook gere maintenant son propre Python.
echo Aucun Python systeme ni alias Microsoft Store n'est utilise.
echo.

rem --- Resolve/install uv ----------------------------------------------------
set "UV="
where uv.exe >nul 2>&1 && set "UV=uv.exe"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"

if not defined UV (
  echo [1/5] Installation du runtime LMNotebook ^(uv^)...
  where winget.exe >nul 2>&1
  if errorlevel 1 (
    echo [ERREUR] winget n'est pas disponible sur ce Windows.
    echo Rien d'autre n'a ete modifie. Envoie-moi cette fenetre.
    pause
    exit /b 1
  )
  winget install --id astral-sh.uv -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
  where uv.exe >nul 2>&1 && set "UV=uv.exe"
  if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
  if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"
) else (
  echo [1/5] Runtime LMNotebook deja present.
)

if not defined UV (
  echo [ERREUR] uv n'a pas ete trouve apres installation.
  echo Rien d'autre n'a ete modifie. Envoie-moi cette fenetre.
  pause
  exit /b 1
)

"%UV%" --version
if errorlevel 1 (
  echo [ERREUR] Le runtime uv ne demarre pas correctement.
  pause
  exit /b 1
)

rem --- FFmpeg ---------------------------------------------------------------
echo [2/5] Verification FFmpeg...
where ffmpeg.exe >nul 2>&1
if errorlevel 1 (
  echo Installation automatique de FFmpeg...
  winget install --id Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%"
)
where ffmpeg.exe >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] FFmpeg reste introuvable. Le moteur n'est pas lance.
  echo Envoie-moi cette fenetre, sans rien bricoler.
  pause
  exit /b 1
)
echo [OK] FFmpeg disponible.

rem --- Private managed Python + venv ---------------------------------------
echo [3/5] Preparation du Python prive LMNotebook 3.12...
if exist "%VENV%\Scripts\python.exe" (
  echo [OK] Environnement deja present.
) else (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.12 "%VENV%"
  if errorlevel 1 goto :venv_error
)

if not exist "%VENV%\Scripts\python.exe" goto :venv_error
"%VENV%\Scripts\python.exe" --version

rem --- Dependencies ---------------------------------------------------------
echo [4/5] Synchronisation des dependances V2...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
  echo [ERREUR] Les dependances du moteur n'ont pas pu etre installees.
  pause
  exit /b 1
)

if not exist "%BACKEND%\.env" if exist "%BACKEND%\.env.example" copy /Y "%BACKEND%\.env.example" "%BACKEND%\.env" >nul

rem --- Launch ---------------------------------------------------------------
echo [5/5] Demarrage de LMNotebook...
start "LMNotebook V2 API" /D "%BACKEND%" cmd /k ""%VENV%\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "LMNotebook Frontend" /D "%ROOT%" cmd /k ""%VENV%\Scripts\python.exe" -m http.server 8008 --bind 127.0.0.1"

timeout /t 4 /nobreak >nul
start "" "http://127.0.0.1:8008"

echo.
echo [OK] LMNotebook lance.
echo Cette fenetre peut etre fermee.
timeout /t 3 /nobreak >nul
exit /b 0

:venv_error
echo.
echo [ERREUR] Le Python prive LMNotebook n'a pas pu etre cree.
echo Ton Python Windows n'est pas concerne et n'a pas ete modifie.
echo Envoie-moi simplement cette fenetre.
pause
exit /b 1
