@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - LAION Larger CLAP Music SETUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "VENV=%RUNTIME%\larger_clap_venv"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

if not exist "%RUNTIME%" mkdir "%RUNTIME%" >nul 2>&1
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - LAION Larger CLAP Music
echo  ISOLATED CANDIDATE D - DOES NOT MODIFY V3, CLAMP3, MUQ, MS-CLAP OR STUDIO
echo ============================================================
echo.
echo Model           : laion/larger_clap_music
echo HF revision     : a0b4534
echo Audio regime    : 48 kHz - exact 10 second clips - CUDA
echo Embedding       : 512D
echo License         : Apache-2.0
echo Runtime pins    : Torch 2.4.1 cu118 + TorchAudio 2.4.1 cu118 + Transformers 4.46.3 + NumPy 1.26.4
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

echo [2/5] Creation environnement Python 3.10 ISOLE Larger CLAP Music...
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

echo [4/5] Installation Transformers + deps benchmark...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" "transformers==4.46.3" "librosa==0.10.2.post1" "soundfile==0.12.1" "numpy==1.26.4" "requests>=2.31,<3" "huggingface-hub>=0.26,<1"
if errorlevel 1 goto :fail

echo [5/5] Verification CUDA + CLAP Transformers + pont Torch/NumPy...
"%VENV%\Scripts\python.exe" -c "import torch,torchaudio,transformers,numpy as np; from transformers import ClapModel,ClapProcessor; assert torch.cuda.is_available(); assert torch.__version__.startswith('2.4.1+cu118'),torch.__version__; assert torchaudio.__version__.startswith('2.4.1+cu118'),torchaudio.__version__; assert torch.version.cuda=='11.8',torch.version.cuda; assert transformers.__version__=='4.46.3',transformers.__version__; assert np.__version__=='1.26.4',np.__version__; p=torch.arange(4,dtype=torch.float32); a=p.numpy(); assert float(a[3])==3.0; print('[OK] GPU:',torch.cuda.get_device_name(0)); print('[OK] Torch',torch.__version__,'TorchAudio',torchaudio.__version__,'CUDA',torch.version.cuda); print('[OK] Transformers',transformers.__version__,'NumPy',np.__version__); print('[OK] ClapModel + ClapProcessor imports + Torch/NumPy bridge active')"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] LAION Larger CLAP Music CANDIDATE D PRET
echo ============================================================
echo.
echo Runtime : %VENV%
echo Model   : laion/larger_clap_music @ a0b4534
echo Policy  : 48 kHz / 5 clips deterministes EXACTS de 10s par morceau
echo License : Apache-2.0
echo.
echo IMPORTANT : le premier benchmark telechargera le checkpoint Hugging Face
echo ^(~776 MB^) et les fichiers tokenizer/processor.
echo Les runs suivants reutiliseront le cache local partage du Model Lab.
echo.
echo Ensuite double-clique :
echo   SONICTRACE_V4_LARGER_CLAP_MUSIC_BENCHMARK.cmd
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
echo  [ERREUR] LAION Larger CLAP Music MODEL LAB SETUP A ECHOUE
echo ============================================================
echo CLaMP3, MuQ-MuLan, Microsoft CLAP, SonicTrace V3 et STUDIO n'ont pas ete modifies.
echo Le runtime Candidate D reste isole dans model_lab\.runtime\larger_clap_venv.
echo Envoie-moi un screenshot de cette fenetre.
echo.
pause
exit /b 1
