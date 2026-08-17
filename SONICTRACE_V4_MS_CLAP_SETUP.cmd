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
echo Reference code  : microsoft/CLAP @ e8a6467b87cd85716e20c6a008126150d9740be0
echo Checkpoint      : microsoft/msclap / CLAP_weights_2023.pth
echo Audio regime    : 44.1 kHz - 7 second clips - CUDA
echo Code license    : MIT
echo Weights license : MS-PL ^(commercially eligible subject to license terms; review before shipping^)
echo Runtime pins    : Torch 2.1.2 cu118 + TorchVision 0.16.2 cu118 + TorchAudio 2.1.2 cu118 + NumPy 1.26.4 + Transformers 4.46.3
echo.

echo [1/6] Verification uv...
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

echo [2/6] Creation environnement Python 3.10 ISOLE MS-CLAP...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.10 "%VENV%"
  if errorlevel 1 goto :fail
)
"%VENV%\Scripts\python.exe" --version
if errorlevel 1 goto :fail

echo [3/6] Installation Microsoft CLAP officiel + deps benchmark...
rem msclap 1.3.3 pulls torchvision 0.16.2 / torch 2.1.2 but leaves torchaudio
rem broad enough for a modern resolver to select a newer binary. On Windows that
rem can create an ABI-mismatched torch/torchaudio pair. Step 4 always repairs the
rem complete PyTorch family after dependency resolution.
"%UV%" pip install --python "%VENV%\Scripts\python.exe" "msclap==1.3.3" "transformers==4.46.3" "librosa==0.10.2.post1" "soundfile==0.12.1" "numpy==1.26.4" "requests>=2.31,<3"
if errorlevel 1 goto :fail

echo [4/6] Verrouillage ABI PyTorch CUDA 11.8 coherent...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --reinstall "torch==2.1.2" "torchvision==0.16.2" "torchaudio==2.1.2" --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 goto :fail

echo [5/6] Re-verrouillage NumPy 1.x compatible avec Torch 2.1.2...
rem The PyTorch reinstall resolves its broad NumPy dependency again and can
rem silently upgrade the venv to NumPy 2.x. Torch 2.1.2 Windows wheels were built
rem against NumPy 1.x, so pin NumPy AFTER the complete PyTorch family is settled.
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --reinstall "numpy==1.26.4"
if errorlevel 1 goto :fail

echo [6/6] Verification CUDA + ABI TorchAudio + pont Torch/NumPy + package...
"%VENV%\Scripts\python.exe" -c "import importlib.metadata as m,torch,torchvision,torchaudio,transformers,numpy as np; assert torch.cuda.is_available(); assert torch.__version__.startswith('2.1.2+cu118'), torch.__version__; assert torchvision.__version__.startswith('0.16.2+cu118'), torchvision.__version__; assert torchaudio.__version__.startswith('2.1.2+cu118'), torchaudio.__version__; assert torch.version.cuda == '11.8', torch.version.cuda; assert np.__version__ == '1.26.4', np.__version__; assert m.version('msclap') == '1.3.3'; assert transformers.__version__ == '4.46.3'; probe=torch.arange(4,dtype=torch.float32); arr=probe.cpu().numpy(); assert arr.shape == (4,) and float(arr[3]) == 3.0; back=torch.from_numpy(np.asarray([1.0,2.0],dtype=np.float32)); assert back.dtype == torch.float32 and back.tolist() == [1.0,2.0]; from msclap import CLAP; print('[OK] GPU:',torch.cuda.get_device_name(0)); print('[OK] Torch',torch.__version__,'TorchVision',torchvision.__version__,'TorchAudio',torchaudio.__version__,'CUDA',torch.version.cuda); print('[OK] Transformers',transformers.__version__,'NumPy',np.__version__); print('[OK] msclap',m.version('msclap'),'CLAP class import + TorchAudio ABI active + Torch/NumPy bridge active')"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] Microsoft CLAP 2023 CANDIDATE C PRET
echo ============================================================
echo.
echo Runtime : %VENV%
echo Model   : microsoft/msclap / CLAP_weights_2023.pth
echo Policy  : 44.1 kHz / 5 clips deterministes de 7s par morceau
echo Stack   : Torch 2.1.2 cu118 / TorchVision 0.16.2 cu118 / TorchAudio 2.1.2 cu118 / NumPy 1.26.4
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
echo Le runtime MS-CLAP reste isole dans model_lab\.runtime\msclap_venv.
echo Envoie-moi un screenshot de cette fenetre.
echo.
pause
exit /b 1
