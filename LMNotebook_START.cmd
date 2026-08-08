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
echo LMNotebook gere son propre Python via uv.
echo Aucun Python systeme ni alias Microsoft Store n'est utilise.
echo.

rem --- Resolve/install uv ----------------------------------------------------
call :resolve_uv
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
  if errorlevel 1 (
    echo [ERREUR] L'installation de uv a echoue.
    pause
    exit /b 1
  )

  call :resolve_uv
) else (
  echo [1/5] Runtime LMNotebook deja present.
)

if not defined UV (
  echo [ERREUR] uv est installe mais son executable reste introuvable.
  echo Aucun autre composant n'est lance. Envoie-moi cette fenetre.
  pause
  exit /b 1
)

echo [OK] Runtime : %UV%
"%UV%" --version
if errorlevel 1 (
  echo [ERREUR] Le runtime uv ne demarre pas correctement.
  pause
  exit /b 1
)

rem --- FFmpeg ---------------------------------------------------------------
echo [2/5] Verification FFmpeg...
call :resolve_ffmpeg
if not defined FFMPEG (
  echo Installation automatique de FFmpeg...
  winget install --id Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 (
    echo [ERREUR] L'installation de FFmpeg a echoue.
    pause
    exit /b 1
  )
  call :resolve_ffmpeg
)

if not defined FFMPEG (
  echo [ERREUR] FFmpeg est installe mais son executable reste introuvable.
  echo Envoie-moi cette fenetre, sans rien bricoler.
  pause
  exit /b 1
)

for %%D in ("%FFMPEG%") do set "PATH=%%~dpD;%PATH%"
echo [OK] FFmpeg : %FFMPEG%

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

rem --- Verified runtime supervisor -----------------------------------------
echo [5/5] Demarrage verifie de LMNotebook...
"%VENV%\Scripts\python.exe" "%ROOT%tools\runtime_manager.py" start
if errorlevel 1 (
  echo.
  echo [ERREUR] LMNotebook n'a pas valide son runtime local.
  echo Le diagnostic utile est affiche ci-dessus et dans le dossier logs.
  pause
  exit /b 1
)

echo.
echo [OK] Runtime local V2 valide.
echo Tu peux fermer cette fenetre.
timeout /t 3 /nobreak >nul
exit /b 0

:resolve_uv
set "UV="
for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined UV set "UV=%%I"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" (
  for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" uv.exe 2^>nul') do if not defined UV set "UV=%%I"
)
exit /b 0

:resolve_ffmpeg
set "FFMPEG="
for /f "delims=" %%I in ('where ffmpeg.exe 2^>nul') do if not defined FFMPEG set "FFMPEG=%%I"
if not defined FFMPEG if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe" set "FFMPEG=%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"
if not defined FFMPEG if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" (
  for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" ffmpeg.exe 2^>nul') do if not defined FFMPEG set "FFMPEG=%%I"
)
exit /b 0

:venv_error
echo.
echo [ERREUR] Le Python prive LMNotebook n'a pas pu etre cree.
echo Ton Python Windows n'est pas concerne et n'a pas ete modifie.
echo Envoie-moi simplement cette fenetre.
pause
exit /b 1
