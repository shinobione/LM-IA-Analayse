@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook Launcher

set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "VENV=%~dp0backend\.venv"
set "STEMS_VENV=%~dp0backend\.venv-stems"
set "HF_HOME=%~dp0backend\models\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1
if not exist "%ROOT%logs" mkdir "%ROOT%logs" >nul 2>&1

echo.
echo ============================================================
echo  LMNotebook Neural Audio Analyzer - SAFE RUNTIME
echo ============================================================
echo.
echo V2-B Neural et V2-D Demucs utilisent deux environnements Python separes.
echo Une couche GPU ne peut plus remplacer les dependances de l'autre.
echo.

call :resolve_uv
if not defined UV (
  echo [1/6] Installation du runtime LMNotebook ^(uv^)...
  where winget.exe >nul 2>&1
  if errorlevel 1 goto :fail
  winget install --id astral-sh.uv -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 goto :fail
  call :resolve_uv
) else (
  echo [1/6] Runtime LMNotebook deja present.
)
if not defined UV goto :fail
echo [OK] Runtime : %UV%
"%UV%" --version
if errorlevel 1 goto :fail

echo [2/6] Verification FFmpeg...
call :resolve_ffmpeg
if not defined FFMPEG (
  winget install --id Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 goto :fail
  call :resolve_ffmpeg
)
if not defined FFMPEG goto :fail
for %%D in ("%FFMPEG%") do set "PATH=%%~dpD;%PATH%"
echo [OK] FFmpeg : %FFMPEG%

echo [3/6] Preparation V2-A/V2-B dans backend\.venv...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.12 "%VENV%"
  if errorlevel 1 goto :fail
)
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements.txt"
if errorlevel 1 goto :fail
if not exist "%BACKEND%\.env" if exist "%BACKEND%\.env.example" copy /Y "%BACKEND%\.env.example" "%BACKEND%\.env" >nul

echo [4/6] Reparation / verification V2-B Neural CUDA...
rem First V2-D bootstrap could have mixed Demucs packages into this environment. Remove them.
"%UV%" pip uninstall --python "%VENV%\Scripts\python.exe" demucs torchaudio >nul 2>&1
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto :neural_warning
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade -r "%BACKEND%\requirements-neural.txt"
if errorlevel 1 goto :neural_warning
"%VENV%\Scripts\python.exe" -c "import torch,transformers; from transformers import ClapModel,ClapProcessor; assert torch.cuda.is_available(); assert torch.__version__.startswith('2.11.0'); print('[OK] V2-B READY |',torch.cuda.get_device_name(0),'| Torch',torch.__version__,'| Transformers',transformers.__version__)"
if errorlevel 1 goto :neural_warning
set "NEURAL_READY=1"
goto :stems_setup

:neural_warning
set "NEURAL_READY=0"
echo [WARN] V2-B Neural indisponible; V2-A reste active.

:stems_setup
echo [5/6] Preparation du runtime ISOLE V2-D Stems...
set "STEMS_READY=0"
if not exist "%STEMS_VENV%\Scripts\python.exe" (
  if exist "%STEMS_VENV%" rmdir /s /q "%STEMS_VENV%"
  "%UV%" venv --python 3.12 "%STEMS_VENV%"
  if errorlevel 1 goto :stems_warning
)
"%UV%" pip install --python "%STEMS_VENV%\Scripts\python.exe" torch==2.11.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto :stems_warning
rem Important: no --upgrade here, otherwise Demucs may replace the pinned CUDA wheels.
"%UV%" pip install --python "%STEMS_VENV%\Scripts\python.exe" -r "%BACKEND%\requirements-stems.txt"
if errorlevel 1 goto :stems_warning
"%STEMS_VENV%\Scripts\python.exe" -c "import torch,torchaudio,demucs; assert torch.cuda.is_available(); assert torch.__version__.startswith('2.11.0'); assert torchaudio.__version__.startswith('2.11.0'); print('[OK] V2-D READY |',torch.cuda.get_device_name(0),'| Torch',torch.__version__,'| Torchaudio',torchaudio.__version__)"
if errorlevel 1 goto :stems_warning
set "STEMS_READY=1"
goto :launch

:stems_warning
set "STEMS_READY=0"
echo [WARN] V2-D Demucs local indisponible. Un worker LAN peut toujours executer les stems.

:launch
echo [6/6] Demarrage verifie de LMNotebook...
"%VENV%\Scripts\python.exe" "%ROOT%tools\runtime_manager.py" start
if errorlevel 1 goto :fail
echo.
if "%NEURAL_READY%"=="1" echo [OK] V2-B Neural CUDA PRETE.
if "%STEMS_READY%"=="1" echo [OK] V2-D Demucs ISOLE PRET.
echo [OK] LMNotebook V2 lance.
timeout /t 4 /nobreak >nul
exit /b 0

:resolve_uv
set "UV="
for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined UV set "UV=%%I"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" uv.exe 2^>nul') do if not defined UV set "UV=%%I"
exit /b 0

:resolve_ffmpeg
set "FFMPEG="
for /f "delims=" %%I in ('where ffmpeg.exe 2^>nul') do if not defined FFMPEG set "FFMPEG=%%I"
if not defined FFMPEG if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe" set "FFMPEG=%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe"
if not defined FFMPEG if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" ffmpeg.exe 2^>nul') do if not defined FFMPEG set "FFMPEG=%%I"
exit /b 0

:fail
echo.
echo [ERREUR] LMNotebook n'a pas pu finaliser son runtime.
echo V2-A/V2-B/V2-D restent confines aux dossiers backend\.venv*.
pause
exit /b 1
