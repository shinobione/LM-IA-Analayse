@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - CLaMP3 SETUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "VENV=%RUNTIME%\venv"
set "CLAMP=%RUNTIME%\clamp3"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

if not exist "%RUNTIME%" mkdir "%RUNTIME%" >nul 2>&1
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - CLaMP3 / MERT-v1-95M
echo  ISOLATED LAB - DOES NOT MODIFY SONICTRACE V3 OR STUDIO
echo ============================================================
echo.

echo [1/6] Verification Git...
where git.exe >nul 2>&1
if errorlevel 1 (
  echo [ERREUR] Git introuvable. Lance d'abord SONICTRACE_INSTALL.cmd.
  goto :fail
)
echo [OK] Git present.

echo [2/6] Verification uv...
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

echo [3/6] Creation environnement Python 3.10 ISOLE...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.10 "%VENV%"
  if errorlevel 1 goto :fail
)
"%VENV%\Scripts\python.exe" --version
if errorlevel 1 goto :fail

echo [4/6] Checkout officiel CLaMP3 epingle...
"%VENV%\Scripts\python.exe" "%LAB%\setup_clamp3.py" --runtime "%RUNTIME%"
if errorlevel 1 goto :fail

echo [5/6] Installation CUDA + dependances CLaMP3...
rem Isolated from backend\.venv. We deliberately follow CLaMP3's CUDA 11.8 path.
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade "torch==2.4.1" "torchaudio==2.4.1" "torchvision==0.19.1" --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 goto :fail
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%CLAMP%\requirements.txt"
if errorlevel 1 goto :fail
"%UV%" pip install --python "%VENV%\Scripts\python.exe" "librosa==0.10.2.post1" "requests>=2.31,<3"
if errorlevel 1 goto :fail

"%VENV%\Scripts\python.exe" -c "import torch,transformers,numpy; assert torch.cuda.is_available(); print('[OK] GPU:',torch.cuda.get_device_name(0)); print('[OK] Torch',torch.__version__,'CUDA',torch.version.cuda,'Transformers',transformers.__version__,'NumPy',numpy.__version__)"
if errorlevel 1 goto :fail

echo [6/6] Generation de la taxonomie multi-axes...
"%VENV%\Scripts\python.exe" "%LAB%\prepare_refs.py" --runtime "%RUNTIME%"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] V4 MODEL LAB PRET
echo ============================================================
echo.
echo Runtime : %RUNTIME%
echo CLaMP3 : commit 9016d2b0c8d12d1aa79c2e0ab201e6822bdc83a8
echo Audio encoder : m-a-p/MERT-v1-95M
echo.
echo IMPORTANT : le PREMIER benchmark telechargera encore les poids
echo CLaMP3 SAAS ^(~2.57 Go^) et MERT depuis Hugging Face.
echo Les lancements suivants reutiliseront les caches locaux.
echo.
echo Ensuite double-clique :
echo   SONICTRACE_V4_MODEL_LAB_BENCHMARK.cmd
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
echo  [ERREUR] V4 MODEL LAB SETUP A ECHOUE
echo ============================================================
echo Aucun runtime SonicTrace V3 ou STUDIO n'a ete modifie.
echo Envoie-moi un screenshot de cette fenetre.
echo.
pause
exit /b 1
