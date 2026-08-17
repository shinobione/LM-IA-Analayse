@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - CLaMP3 BENCHMARK

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "LABPY=%RUNTIME%\venv\Scripts\python.exe"
set "SCRIPT=%LAB%\run_clamp3_benchmark.py"
set "LIST=%TEMP%\sonictrace-v4-model-lab-files.txt"
set "HF_HOME=%RUNTIME%\huggingface"

if not exist "%LABPY%" (
  echo.
  echo [ERREUR] Le V4 Model Lab n'est pas installe.
  echo Lance d'abord : SONICTRACE_V4_MODEL_LAB_SETUP.cmd
  echo.
  pause
  exit /b 1
)

if exist "%LIST%" del /q "%LIST%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - A/B AUDIO-ONLY
necho  CLaMP3 SAAS + MERT-v1-95M - RTX CUDA
necho ============================================================
echo.
echo Choisis un ou plusieurs WAV/MP3 dans la fenetre qui s'ouvre.
echo Pour notre premier round : THICK, Tachy Psychia,
echo Stick to You et Tinh Bolero Cho Tran sont parfaits.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='SonicTrace V4 Model Lab - Choisir les morceaux'; $d.Filter='Audio (*.wav;*.mp3;*.flac;*.ogg)|*.wav;*.mp3;*.flac;*.ogg|Tous les fichiers (*.*)|*.*'; $d.Multiselect=$true; if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){[System.IO.File]::WriteAllLines($env:LIST,$d.FileNames)}"

if not exist "%LIST%" (
  echo [INFO] Aucun fichier selectionne.
  timeout /t 2 /nobreak >nul
  exit /b 0
)

echo.
echo [INFO] Benchmark en cours...
echo [INFO] Premier lancement : CLaMP3 ^(~2.57 Go^) + MERT peuvent etre telecharges.
echo [INFO] Les resultats seront dans model_lab\results\
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$files=Get-Content -LiteralPath $env:LIST; & $env:LABPY $env:SCRIPT @files; exit $LASTEXITCODE"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo [ERREUR] Le benchmark a echoue ^(code %RC%^\).
  echo Envoie-moi un screenshot de cette fenetre.
  echo.
  pause
  exit /b %RC%
)

echo.
echo ============================================================
echo  [OK] BENCHMARK TERMINE
necho ============================================================
echo.
start "" "%LAB%\results"
pause
exit /b 0
