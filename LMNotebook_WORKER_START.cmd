@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook GPU Worker

set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "VENV=%~dp0backend\.venv"
set "STEMS_VENV=%~dp0backend\.venv-stems"
set "HF_HOME=%~dp0backend\models\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  LMNotebook - GPU WORKER LAN
echo ============================================================
echo.
echo V2-B Neural et V2-D Demucs utilisent maintenant deux environnements separes.
echo Aucun frontend n'est lance ici.
echo.

call :resolve_uv
if not defined UV (
  echo [1/7] Installation du runtime uv...
  winget install --id astral-sh.uv -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  call :resolve_uv
)
if not defined UV goto :fail
echo [1/7] Runtime OK : %UV%

call :resolve_ffmpeg
if not defined FFMPEG (
  echo [2/7] Installation FFmpeg...
  winget install --id Gyan.FFmpeg -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  call :resolve_ffmpeg
)
if not defined FFMPEG goto :fail
for %%D in ("%FFMPEG%") do set "PATH=%%~dpD;%PATH%"
echo [2/7] FFmpeg OK.

echo [3/7] Environnement Python principal V2-A/V2-B...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.12 "%VENV%"
  if errorlevel 1 goto :fail
)

echo [4/7] Reparation / synchronisation V2-A + V2-B...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements.txt"
if errorlevel 1 goto :fail
rem Remove packages that were accidentally mixed into the CLAP environment by the first V2-D bootstrap.
"%UV%" pip uninstall --python "%VENV%\Scripts\python.exe" demucs torchaudio >nul 2>&1
rem Force the known CUDA build back in case Demucs previously replaced it with a PyPI CPU/default build.
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto :fail
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade -r "%BACKEND%\requirements-neural.txt"
if errorlevel 1 goto :fail
"%VENV%\Scripts\python.exe" -c "import torch,transformers; from transformers import ClapModel,ClapProcessor; assert torch.cuda.is_available(); assert torch.__version__.startswith('2.11.0'); print('[OK] V2-B Neural CUDA:',torch.cuda.get_device_name(0),'| Torch',torch.__version__,'| Transformers',transformers.__version__)"
if errorlevel 1 goto :fail

echo [5/7] Creation du runtime ISOLE V2-D Stems...
if not exist "%STEMS_VENV%\Scripts\python.exe" (
  if exist "%STEMS_VENV%" rmdir /s /q "%STEMS_VENV%"
  "%UV%" venv --python 3.12 "%STEMS_VENV%"
  if errorlevel 1 goto :fail
)

echo [6/7] Installation PyTorch / torchaudio CUDA + Demucs dans .venv-stems...
"%UV%" pip install --python "%STEMS_VENV%\Scripts\python.exe" torch==2.11.0 torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128
if errorlevel 1 goto :fail
rem Do NOT use --upgrade here: installed CUDA torch/torchaudio must stay pinned.
"%UV%" pip install --python "%STEMS_VENV%\Scripts\python.exe" -r "%BACKEND%\requirements-stems.txt"
if errorlevel 1 goto :fail
"%STEMS_VENV%\Scripts\python.exe" -c "import torch,torchaudio,demucs; assert torch.cuda.is_available(); assert torch.__version__.startswith('2.11.0'); assert torchaudio.__version__.startswith('2.11.0'); print('[OK] V2-D Demucs ISOLE:',torch.cuda.get_device_name(0),'| Torch',torch.__version__,'| Torchaudio',torchaudio.__version__)"
if errorlevel 1 goto :fail

echo [7/7] Pare-feu LAN + demarrage worker...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$name='LMNotebook GPU Worker 8001'; if(-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)){ try { New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8001 -Profile Private -RemoteAddress LocalSubnet | Out-Null } catch {} }" >nul 2>&1
set "LMN_WORKER_PORT=8001"
"%VENV%\Scripts\python.exe" "%ROOT%tools\worker_runtime.py" stop >nul 2>&1
"%VENV%\Scripts\python.exe" "%ROOT%tools\worker_runtime.py" start
if errorlevel 1 goto :fail

echo.
echo [OK] Worker GPU actif.
echo [OK] V2-B CLAP et V2-D Demucs sont isoles l'un de l'autre.
for /f "delims=" %%I in ('powershell -NoProfile -Command "(Get-NetIPAddress -AddressFamily IPv4 ^| ? {$_.IPAddress -notlike '169.254*' -and $_.IPAddress -ne '127.0.0.1'} ^| Select-Object -First 1 -ExpandProperty IPAddress)"') do set "LANIP=%%I"
if defined LANIP echo [INFO] Adresse worker : http://%LANIP%:8001
echo.
timeout /t 5 /nobreak >nul
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
echo [ERREUR] Le worker n'a pas pu etre initialise.
echo Le coordinateur n'est pas affecte. Envoie-moi cette fenetre.
pause
exit /b 1
