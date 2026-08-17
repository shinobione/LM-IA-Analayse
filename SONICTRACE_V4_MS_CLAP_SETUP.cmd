@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - Microsoft CLAP 2023 SETUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "VENV=%RUNTIME%\msclap_venv"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

if not exist "%RUNTIME%" mkdir "%RUNTIME%" >nul 2>&1
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - Microsoft CLAP 2023
echo  ISOLATED CANDIDATE C - DOES NOT MODIFY V3, CLAMP3, MUQ OR STUDIO
echo ============================================================
echo.
echo Official package : msclap 1.3.3
echo Official code    : microsoft/CLAP @ e8a6467b87cd85716e20c6a008126150d9740be0
echo Checkpoint       : microsoft/msclap / CLAP_weights_2023.pth
echo Audio regime     : 44.1 kHz - 7 second clips - CUDA
echo Code license     : MIT
echo Weights license  : MS-PL ^(commercially eligible subject to license terms; review before shipping^)
echo Runtime pins     : Torch 2.4.1 cu118 + Transformers 4.46.3
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

echo [2/5] Creation environnement Python 3.10 ISOLE MS-CLAP...
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

echo [4/5] Installation Microsoft CLAP officiel + deps benchmark...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" "msclap==1.3.3" "transformers==4.46.3" "librosa==0.10.2.post1" "soundfile==0.12.1" "numpy==1.26.4" "requests>=2.31,<3"
if errorlevel 1 goto :fail

echo [5/5] Verification CUDA + package + backend...
"%VENV%\Scripts\python.exe" -c "import importlib.metadata as m,torch,transformers,numpy; from msclap import CLAP; assert torch.cuda.is_available(); assert m.version('msclap') == '1.3.3'; assert transformers.__version__ == '4.46.3'; print('[OK] GPU:',torch.cuda.get_device_name(0)); print('[OK] Torch',torch.__version__,'CUDA',torch.version.cuda,'Transformers',transformers.__version__,'NumPy',numpy.__version__); print('[OK] msclap',m.version('msclap'),'CLAP class import')"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] Microsoft CLAP 2023 CANDIDATE C PRET
echo ============================================================
echo.
echo Runtime : %VENV%
echo Model   : microsoft/msclap / CLAP_weights_2023.pth
 echo Policy  : 44.1 kHz / 5 clips deterministes de 7s par morceau
 echo License : MIT code / MS-PL weights
 echo.
echo IMPORTANT : le premier benchmark telechargera le checkpoint 2023
 echo Microsoft CLAP depuis Hugging Face ^(~690 MB^).
echo Les runs suivants reutiliseront le cache local partage du Model Lab.
echo.
echo Ensuite double-clique :
echo   SONICTRACE_V4_MS_CLAP_BENCHMARK.cmd
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
echo  [ERREUR] Microsoft CLAP MODEL LAB SETUP A ECHOUE
echo ============================================================
echo CLaMP3, MuQ-MuLan, SonicTrace V3 et STUDIO n'ont pas ete modifies.
echo Envoie-moi un screenshot de cette fenetre.
echo.
pause
exit /b 1
