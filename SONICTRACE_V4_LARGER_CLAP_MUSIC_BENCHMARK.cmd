@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - LAION Larger CLAP Music BENCHMARK

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "LABPY=%RUNTIME%\larger_clap_venv\Scripts\python.exe"
set "SCRIPT=%LAB%\run_larger_clap_music_benchmark.py"
set "LAUNCHER=%LAB%\launch_benchmark.py"
set "LIST=%TEMP%\sonictrace-v4-larger-clap-music-files.txt"
set "RESULTS=%LAB%\results"
set "LOG=%RESULTS%\larger-clap-music-last-run.log"
set "ERRLOG=%RESULTS%\larger-clap-music-last-error.txt"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%RUNTIME%\larger_clap_venv\Scripts;%PATH%"
set "VIRTUAL_ENV=%RUNTIME%\larger_clap_venv"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"

if not exist "%LABPY%" (
  echo.
  echo [ERREUR] Le candidat LAION Larger CLAP Music n'est pas installe.
  echo Lance d'abord : SONICTRACE_V4_LARGER_CLAP_MUSIC_SETUP.cmd
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
echo  SONICTRACE V4 MODEL LAB - CANDIDATE D
echo  LAION Larger CLAP Music - 48kHz - CUDA - Apache-2.0
echo ============================================================
echo.
echo Choisis EXACTEMENT les memes WAV/MP3 que pour MuQ, CLaMP3 et MS-CLAP.
echo Idealement : THICK, Tachy Psychia, Stick to You,
echo et Tinh Bolero Cho Tran ensemble.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='SonicTrace V4 Larger CLAP Music - Choisir les morceaux'; $d.Filter='Audio (*.wav;*.mp3)|*.wav;*.mp3'; $d.Multiselect=$true; if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){[System.IO.File]::WriteAllLines($env:LIST,$d.FileNames)}"

if not exist "%LIST%" (
  echo [INFO] Aucun fichier selectionne.
  timeout /t 2 /nobreak >nul
  exit /b 0
)

echo.
echo [OK] Selection recue :
for /f "usebackq delims=" %%F in ("%LIST%") do echo      %%F
echo.
echo [INFO] Benchmark LAION Larger CLAP Music en cours...
echo [INFO] Premier lancement : checkpoint ^(~776 MB^) + processor/tokenizer peuvent etre telecharges.
echo [INFO] Chaque morceau = 5 fenetres deterministes EXACTES de 10 secondes.
echo [INFO] Le rand_trunc du processor officiel est neutralise avant inference.
echo [INFO] Cette fenetre RESTERA OUVERTE en cas d'erreur.
echo [INFO] Log permanent : model_lab\results\larger-clap-music-last-run.log
echo.

"%LABPY%" "%LAUNCHER%" --engine-label "LAION Larger CLAP Music" --runner "%SCRIPT%" --file-list "%LIST%" --log "%LOG%" --error-log "%ERRLOG%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ============================================================
  echo  [ERREUR] BENCHMARK Larger CLAP Music ECHOUE - CODE %RC%
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
  echo Envoie-moi larger-clap-music-last-error.txt si ca plante.
  echo Cette fenetre ne se fermera pas toute seule.
  echo.
  pause
  exit /b %RC%
)

echo.
echo ============================================================
echo  [OK] BENCHMARK LAION Larger CLAP Music TERMINE
echo ============================================================
echo.
echo Resultats : %RESULTS%
start "" "%RESULTS%"
pause
exit /b 0
