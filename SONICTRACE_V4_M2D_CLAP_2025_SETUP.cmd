@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - M2D-CLAP 2025 SETUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "VENV=%RUNTIME%\m2d_clap_2025_venv"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "TOKENIZERS_PARALLELISM=false"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

if not exist "%RUNTIME%" mkdir "%RUNTIME%" >nul 2>&1
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - M2D-CLAP 2025
echo  ISOLATED CANDIDATE F - LAB ONLY - NO V3 / CATALOG / STUDIO CHANGE
echo ============================================================
echo.
echo Upstream         : nttcslab/m2d @ 3d0c4de9447c404a8d3f9f37e04f53bc902e09b3
echo Release          : v0.5.0
echo Model            : m2d_clap_vit_base-80x1001p16x16p16kpBpTI-2025
echo Checkpoint       : checkpoint-30.pth
echo Audio regime     : 16 kHz - exact 10 second clips - CUDA
echo Shared embedding : 768D
echo License status   : custom LICENSE.pdf - UNRESOLVED - LAB ONLY
echo Runtime pins     : Torch 2.4.1 cu118 / TorchVision 0.19.1 / TorchAudio 2.4.1
echo                   Transformers 4.46.3 / NumPy 1.26.4 / timm 1.0.19
echo.

echo [1/5] Verification uv...
call :resolve_uv
if not defined UV (
  echo [..] Installation automatique de uv...
  where winget.exe >nul 2>&1
  if errorlevel 1 goto :fail
  winget install --id astral-sh.uv -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 goto :fail
  call :resolve_uv
)
if not defined UV goto :fail
echo [OK] uv : %UV%

echo [2/5] Creation environnement Python 3.10 ISOLE M2D-CLAP 2025...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.10 "%VENV%"
  if errorlevel 1 goto :fail
)
"%VENV%\Scripts\python.exe" --version
if errorlevel 1 goto :fail

echo [3/5] Installation dependances M2D-CLAP epinglees...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade ^
  "numpy==1.26.4" ^
  "transformers==4.46.3" ^
  "timm==1.0.19" ^
  "nnAudio==0.3.3" ^
  "einops==0.8.1" ^
  "librosa==0.11.0" ^
  "soundfile==0.13.1"
if errorlevel 1 goto :fail

echo [4/5] Verrouillage PyTorch CUDA 11.8 + ABI NumPy...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --reinstall ^
  "torch==2.4.1" "torchvision==0.19.1" "torchaudio==2.4.1" ^
  --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 goto :fail
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --reinstall "numpy==1.26.4"
if errorlevel 1 goto :fail

echo [5/5] Assets officiels + chargement CUDA REEL + embeddings audio/texte...
"%VENV%\Scripts\python.exe" "%LAB%\setup_m2d_clap_2025.py" --runtime "%RUNTIME%"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] M2D-CLAP 2025 CANDIDATE F PRET
echo ============================================================
echo.
echo Runtime : %VENV%
echo Policy  : 16 kHz / 5 clips deterministes EXACTS de 10s par morceau
echo License : custom LICENSE.pdf - NON QUALIFIE PRODUIT - LAB ONLY
echo.
echo Ensuite double-clique :
echo   SONICTRACE_V4_M2D_CLAP_2025_BENCHMARK.cmd
echo.
pause
exit /b 0

:resolve_uv
set "UV="
for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined UV set "UV=%%I"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" uv.exe 2^>nul') do if not defined UV set "UV=%%I"
exit /b 0

:fail
echo.
echo ============================================================
echo  [ERREUR] M2D-CLAP 2025 MODEL LAB SETUP A ECHOUE
echo ============================================================
echo CLaMP3, MuQ-MuLan, Microsoft CLAP, LAION candidates, SonicTrace V3, Catalogue et STUDIO n'ont pas ete modifies.
echo Le runtime Candidate F reste isole dans model_lab\.runtime\m2d_clap_2025_venv.
echo Cette fenetre reste ouverte : envoie-moi le dernier bloc d'erreur.
echo.
pause
exit /b 1
