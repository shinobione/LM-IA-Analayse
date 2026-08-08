@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title LMNotebook GPU Worker

set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "VENV=%~dp0backend\.venv"
set "HF_HOME=%~dp0backend\models\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  LMNotebook - GPU WORKER LAN
echo ============================================================
echo.
echo Ce PC devient un worker GPU LMNotebook sur le reseau local.
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

echo [3/7] Environnement Python prive...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.12 "%VENV%"
  if errorlevel 1 goto :fail
)

echo [4/7] Dependances backend...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements.txt"
if errorlevel 1 goto :fail

echo [5/7] CUDA + Neural...
"%VENV%\Scripts\python.exe" -c "import torch; import sys; sys.exit(0 if torch.cuda.is_available() else 3)" >nul 2>&1
if errorlevel 1 (
  "%UV%" pip install --python "%VENV%\Scripts\python.exe" torch==2.11.0 --index-url https://download.pytorch.org/whl/cu128
  if errorlevel 1 goto :fail
)
"%UV%" pip install --python "%VENV%\Scripts\python.exe" -r "%BACKEND%\requirements-neural.txt"
if errorlevel 1 goto :fail
"%VENV%\Scripts\python.exe" -c "import torch; from transformers import ClapModel, ClapProcessor; assert torch.cuda.is_available(); x=torch.randn((64,64),device='cuda'); y=x@x; torch.cuda.synchronize(); print('[OK] Neural CUDA:',torch.cuda.get_device_name(0))"
if errorlevel 1 goto :fail

echo [6/7] Demucs + torchaudio CUDA...
"%VENV%\Scripts\python.exe" -c "import torch,torchaudio,demucs; assert torch.cuda.is_available()" >nul 2>&1
if errorlevel 1 (
  "%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade torchaudio==2.11.0 --index-url https://download.pytorch.org/whl/cu128
  if errorlevel 1 goto :fail
  "%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade -r "%BACKEND%\requirements-stems.txt"
  if errorlevel 1 goto :fail
)
"%VENV%\Scripts\python.exe" -c "import torch,torchaudio,demucs; assert torch.cuda.is_available(); print('[OK] Demucs htdemucs:',torch.cuda.get_device_name(0))"
if errorlevel 1 goto :fail

echo [7/7] Pare-feu LAN + demarrage worker...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$name='LMNotebook GPU Worker 8001'; if(-not (Get-NetFirewallRule -DisplayName $name -ErrorAction SilentlyContinue)){ try { New-NetFirewallRule -DisplayName $name -Direction Inbound -Action Allow -Protocol TCP -LocalPort 8001 -Profile Private -RemoteAddress LocalSubnet | Out-Null } catch {} }" >nul 2>&1
set "LMN_WORKER_PORT=8001"
"%VENV%\Scripts\python.exe" "%ROOT%tools\worker_runtime.py" stop >nul 2>&1
"%VENV%\Scripts\python.exe" "%ROOT%tools\worker_runtime.py" start
if errorlevel 1 goto :fail

echo.
echo [OK] Worker GPU LMNotebook actif + Demucs READY.
echo [INFO] Le coordinateur RTX3060 le detectera automatiquement sur le LAN.
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
echo Le PC principal n'est pas affecte. Envoie-moi cette fenetre.
pause
exit /b 1
