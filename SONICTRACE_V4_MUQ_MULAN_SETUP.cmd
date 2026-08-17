@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - MuQ-MuLan SETUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "VENV=%RUNTIME%\muq_venv"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

if not exist "%RUNTIME%" mkdir "%RUNTIME%" >nul 2>&1
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - MuQ-MuLan 700M
echo  ISOLATED CHALLENGER - DOES NOT MODIFY V3, CLAMP3 OR STUDIO
echo ============================================================
echo.
echo Official checkpoint: OpenMuQ/MuQ-MuLan-large
echo Audio: 24 kHz - fp32 - 10 second clip model
echo Weights license: CC-BY-NC-4.0 ^(non-commercial^)
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

echo [2/5] Creation environnement Python 3.10 ISOLE MuQ...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.10 "%VENV%"
  if errorlevel 1 goto :fail
)
"%VENV%\Scripts\python.exe" --version
if errorlevel 1 goto :fail

echo [3/5] Installation PyTorch CUDA 11.8...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade "torch==2.4.1" "torchaudio==2.4.1" --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 goto :fail

echo [4/5] Installation MuQ officiel + audio deps...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" "muq==0.1.0" "librosa==0.10.2.post1" "soundfile==0.12.1" "numpy<2" "requests>=2.31,<3"
if errorlevel 1 goto :fail

echo [5/5] Verification CUDA + package...
"%VENV%\Scripts\python.exe" -c "import torch,muq,numpy; assert torch.cuda.is_available(); print('[OK] GPU:',torch.cuda.get_device_name(0)); print('[OK] Torch',torch.__version__,'CUDA',torch.version.cuda,'NumPy',numpy.__version__); print('[OK] MuQ package import')"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] MuQ-MuLan CHALLENGER PRET
echo ============================================================
echo.
echo Runtime : %VENV%
echo Model   : OpenMuQ/MuQ-MuLan-large ^(~700M, 512D^)
echo Policy  : fp32 / 24 kHz / 5 clips deterministes de 10s par morceau
echo.
echo IMPORTANT : le premier benchmark telechargera les checkpoints

echo MuQ-MuLan / MuQ depuis Hugging Face ^(plusieurs Go^).
echo Les runs suivants reutiliseront le cache local partage du Model Lab.
echo.
echo Ensuite double-clique :
echo   SONICTRACE_V4_MUQ_MULAN_BENCHMARK.cmd
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
echo  [ERREUR] MuQ-MuLan MODEL LAB SETUP A ECHOUE
echo ============================================================
echo CLaMP3, SonicTrace V3 et STUDIO n'ont pas ete modifies.
echo Envoie-moi un screenshot de cette fenetre.
echo.
pause
exit /b 1
