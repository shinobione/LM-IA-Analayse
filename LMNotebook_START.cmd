@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook Launcher

set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "VENV=%~dp0backend\.venv"
set "HF_HOME=%~dp0backend\models\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  LMNotebook Neural Audio Analyzer - SAFE RUNTIME
echo ============================================================
echo.
echo LMNotebook gere son propre Python via uv.
echo La couche GPU V2-B reste optionnelle: elle ne peut pas casser V2-A.
echo.

rem --- Resolve/install uv ----------------------------------------------------
call :resolve_uv
if not defined UV (
  echo [1/6] Installation du runtime LMNotebook ^(uv^)...
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
  echo [1/6] Runtime LMNotebook deja present.
)

if not defined UV (
  echo [ERREUR] uv est installe mais son executable reste introuvable.
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
echo [2/6] Verification FFmpeg...
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
echo [3/6] Preparation du Python prive LMNotebook 3.12...
if exist "%VENV%\Scripts\python.exe" (
  echo [OK] Environnement deja present.
) else (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.12 "%VENV%"
  if errorlevel 1 goto :venv_error
)

if not exist "%VENV%\Scripts\python.exe" goto :venv_error
"%VENV%\Scripts\python.exe" --version

rem --- Base dependencies ----------------------------------------------------
echo [4/6] Synchronisation des dependances V2-A...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements.txt"
if errorlevel 1 (
  echo [ERREUR] Les dependances du moteur V2-A n'ont pas pu etre installees.
  pause
  exit /b 1
)

if not exist "%BACKEND%\.env" if exist "%BACKEND%\.env.example" copy /Y "%BACKEND%\.env.example" "%BACKEND%\.env" >nul

rem --- Optional CUDA / neural layer ----------------------------------------
echo [5/6] Verification V2-B Neural / CUDA...
"%VENV%\Scripts\python.exe" -c "import torch, transformers, librosa; import sys; sys.exit(0 if torch.cuda.is_available() else 3)" >nul 2>&1
if errorlevel 1 (
  echo [INFO] Premier branchement neural: installation PyTorch CUDA 12.8 + CLAP runtime.
  echo [INFO] C'est le gros telechargement initial; les lancements suivants seront rapides.
  "%UV%" pip install --python "%VENV%\Scripts\python.exe" torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
  if errorlevel 1 goto :neural_warning
  "%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements-neural.txt"
  if errorlevel 1 goto :neural_warning
)

rem Real CUDA smoke test: allocate and execute a tiny matrix multiply on the GPU.
"%VENV%\Scripts\python.exe" -c "import torch, transformers, librosa; import sys; assert torch.cuda.is_available(); x=torch.randn((128,128),device='cuda'); y=x@x; torch.cuda.synchronize(); print('[OK] V2-B CUDA:', torch.__version__, '| CUDA', torch.version.cuda, '|', torch.cuda.get_device_name(0), '| test', float(y[0,0])); sys.exit(0)"
if errorlevel 1 goto :neural_warning
set "NEURAL_READY=1"
goto :launch

:neural_warning
echo.
echo [WARN] La couche Neural V2-B n'est pas encore disponible.
echo [WARN] V2-A reste 100%% fonctionnelle; LMNotebook va quand meme demarrer.
echo [WARN] Aucun pilote NVIDIA ni composant Windows n'a ete modifie.
echo.
set "NEURAL_READY=0"

:launch
rem --- Verified runtime supervisor -----------------------------------------
echo [6/6] Demarrage verifie de LMNotebook...
"%VENV%\Scripts\python.exe" "%ROOT%tools\runtime_manager.py" start
if errorlevel 1 (
  echo.
  echo [ERREUR] LMNotebook n'a pas valide son runtime local.
  echo Le diagnostic utile est affiche ci-dessus et dans le dossier logs.
  pause
  exit /b 1
)

echo.
if "%NEURAL_READY%"=="1" (
  echo [OK] V2-A + V2-B CUDA pretes. Le modele CLAP sera telecharge au premier Deep Scan.
  echo [INFO] Cache du modele: %HF_HOME%
) else (
  echo [OK] V2-A prete. Couche Neural en attente de diagnostic.
)
echo Tu peux fermer cette fenetre.
timeout /t 4 /nobreak >nul
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
