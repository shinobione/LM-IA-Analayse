@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - CLaMP3 BENCHMARK

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "LABPY=%RUNTIME%\venv\Scripts\python.exe"
set "SCRIPT=%LAB%\run_clamp3_benchmark.py"
set "LAUNCHER=%LAB%\launch_benchmark.py"
set "LIST=%TEMP%\sonictrace-v4-model-lab-files.txt"
set "RESULTS=%LAB%\results"
set "LOG=%RESULTS%\last-run.log"
set "ERRLOG=%RESULTS%\last-error.txt"
set "HF_HOME=%RUNTIME%\huggingface"

rem CLaMP3 helper scripts invoke nested commands using the literal name `python`.
rem Force every child process to resolve that name inside the isolated Model Lab venv.
set "PATH=%RUNTIME%\venv\Scripts;%PATH%"
set "VIRTUAL_ENV=%RUNTIME%\venv"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"

if not exist "%LABPY%" (
  echo.
  echo [ERREUR] Le V4 Model Lab n'est pas installe.
  echo Lance d'abord : SONICTRACE_V4_MODEL_LAB_SETUP.cmd
  echo.
  pause
  exit /b 1
)

if not exist "%LAUNCHER%" (
  echo.
  echo [ERREUR] Launcher V4 manquant :
  echo %LAUNCHER%
  echo Lance SONICTRACE_UPDATE.cmd puis reessaie.
  echo.
  pause
  exit /b 1
)

if not exist "%RESULTS%" mkdir "%RESULTS%" >nul 2>&1
if exist "%LIST%" del /q "%LIST%" >nul 2>&1
if exist "%LOG%" del /q "%LOG%" >nul 2>&1
if exist "%ERRLOG%" del /q "%ERRLOG%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - A/B AUDIO-ONLY
echo  CLaMP3 SAAS + MERT-v1-95M - RTX CUDA
echo ============================================================
echo.
echo Choisis un ou plusieurs WAV/MP3 dans la fenetre qui s'ouvre.
echo Pour notre premier round : THICK, Tachy Psychia,
echo Stick to You et Tinh Bolero Cho Tran sont parfaits.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='SonicTrace V4 Model Lab - Choisir les morceaux'; $d.Filter='Audio CLaMP3 (*.wav;*.mp3)|*.wav;*.mp3'; $d.Multiselect=$true; if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){[System.IO.File]::WriteAllLines($env:LIST,$d.FileNames)}"

if not exist "%LIST%" (
  echo [INFO] Aucun fichier selectionne.
  timeout /t 2 /nobreak >nul
  exit /b 0
)

echo.
echo [OK] Selection recue :
for /f "usebackq delims=" %%F in ("%LIST%") do echo      %%F
echo.
echo [INFO] Benchmark en cours...
echo [INFO] Premier lancement : CLaMP3 ^(~2.57 Go^) + MERT peuvent etre telecharges.
echo [INFO] Cette fenetre RESTERA OUVERTE en cas d'erreur.
echo [INFO] Log permanent : model_lab\results\last-run.log
echo.

"%LABPY%" "%LAUNCHER%" --runner "%SCRIPT%" --file-list "%LIST%" --log "%LOG%" --error-log "%ERRLOG%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ============================================================
  echo  [ERREUR] BENCHMARK V4 ECHOUE - CODE %RC%
  echo ============================================================
  echo.
  echo Log complet :
  echo   %LOG%
  if exist "%ERRLOG%" (
    echo Diagnostic :
    echo   %ERRLOG%
    echo.
    echo [INFO] Ouverture automatique du diagnostic dans le Bloc-notes...
    start "" notepad.exe "%ERRLOG%"
  )
  echo.
  echo Fais-moi un screenshot de cette fenetre OU envoie last-error.txt.
  echo Cette fenetre ne se fermera pas toute seule.
  echo.
  pause
  exit /b %RC%
)

echo.
echo ============================================================
echo  [OK] BENCHMARK TERMINE
echo ============================================================
echo.
echo Resultats : %RESULTS%
start "" "%RESULTS%"
pause
exit /b 0
