@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - Microsoft CLAP 2023 BENCHMARK

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "LABPY=%RUNTIME%\msclap_venv\Scripts\python.exe"
set "SCRIPT=%LAB%\run_ms_clap_benchmark.py"
set "LAUNCHER=%LAB%\launch_benchmark.py"
set "LIST=%TEMP%\sonictrace-v4-msclap-files.txt"
set "RESULTS=%LAB%\results"
set "LOG=%RESULTS%\msclap-last-run.log"
set "ERRLOG=%RESULTS%\msclap-last-error.txt"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%RUNTIME%\msclap_venv\Scripts;%PATH%"
set "VIRTUAL_ENV=%RUNTIME%\msclap_venv"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"

if not exist "%LABPY%" (
  echo.
  echo [ERREUR] Le candidat Microsoft CLAP 2023 n'est pas installe.
  echo Lance d'abord : SONICTRACE_V4_MS_CLAP_SETUP.cmd
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
echo  SONICTRACE V4 MODEL LAB - CANDIDATE C
echo  Microsoft CLAP 2023 - 44.1kHz - CUDA - MS-PL weights
echo ============================================================
echo.
echo Choisis EXACTEMENT les memes WAV/MP3 que pour MuQ et CLaMP3.
echo Idealement : THICK, Tachy Psychia, Stick to You,
echo et Tinh Bolero Cho Tran ensemble.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='SonicTrace V4 Microsoft CLAP - Choisir les morceaux'; $d.Filter='Audio (*.wav;*.mp3)|*.wav;*.mp3'; $d.Multiselect=$true; if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){[System.IO.File]::WriteAllLines($env:LIST,$d.FileNames)}"

if not exist "%LIST%" (
  echo [INFO] Aucun fichier selectionne.
  timeout /t 2 /nobreak >nul
  exit /b 0
)

echo.
echo [OK] Selection recue :
for /f "usebackq delims=" %%F in ("%LIST%") do echo      %%F
echo.
echo [INFO] Benchmark Microsoft CLAP 2023 en cours...
echo [INFO] Premier lancement : checkpoint 2023 ^(~690 MB^) + GPT-2 peuvent etre telecharges.
echo [INFO] Chaque morceau = 5 fenetres deterministes de 7 secondes.
echo [INFO] Le crop aleatoire du wrapper officiel est neutralise par staging de clips EXACTS de 7s.
echo [INFO] Cette fenetre RESTERA OUVERTE en cas d'erreur.
echo [INFO] Log permanent : model_lab\results\msclap-last-run.log
echo.

"%LABPY%" "%LAUNCHER%" --engine-label "Microsoft CLAP 2023" --runner "%SCRIPT%" --file-list "%LIST%" --log "%LOG%" --error-log "%ERRLOG%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ============================================================
  echo  [ERREUR] BENCHMARK Microsoft CLAP ECHOUE - CODE %RC%
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
  echo Envoie-moi msclap-last-error.txt si ca plante.
  echo Cette fenetre ne se fermera pas toute seule.
  echo.
  pause
  exit /b %RC%
)

echo.
echo ============================================================
echo  [OK] BENCHMARK Microsoft CLAP 2023 TERMINE
echo ============================================================
echo.
echo Resultats : %RESULTS%
start "" "%RESULTS%"
pause
exit /b 0
