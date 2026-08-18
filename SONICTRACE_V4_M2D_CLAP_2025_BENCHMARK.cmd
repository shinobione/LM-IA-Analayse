@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - M2D-CLAP 2025 BENCHMARK

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "LABPY=%RUNTIME%\m2d_clap_2025_venv\Scripts\python.exe"
set "SCRIPT=%LAB%\run_m2d_clap_2025_benchmark.py"
set "LAUNCHER=%LAB%\launch_benchmark.py"
set "LIST=%TEMP%\sonictrace-v4-m2d-clap-2025-files.txt"
set "RESULTS=%LAB%\results"
set "LOG=%RESULTS%\m2d-clap-2025-last-run.log"
set "ERRLOG=%RESULTS%\m2d-clap-2025-last-error.txt"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%RUNTIME%\m2d_clap_2025_venv\Scripts;%PATH%"
set "VIRTUAL_ENV=%RUNTIME%\m2d_clap_2025_venv"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "TOKENIZERS_PARALLELISM=false"

if not exist "%LABPY%" (
  echo.
  echo [ERREUR] Candidate F M2D-CLAP 2025 n'est pas installe.
  echo Lance d'abord : SONICTRACE_V4_M2D_CLAP_2025_SETUP.cmd
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
echo  SONICTRACE V4 MODEL LAB - CANDIDATE F
echo  M2D-CLAP 2025 - 768D - 16kHz - CUDA - LAB ONLY
echo ============================================================
echo.
echo Choisis EXACTEMENT les memes WAV/MP3 que pour les autres candidats.
echo Idealement : THICK, Tachy Psychia, Stick to You,
echo et Tinh Bolero Cho Tran ensemble.
echo.

powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "Add-Type -AssemblyName System.Windows.Forms; $d=New-Object System.Windows.Forms.OpenFileDialog; $d.Title='SonicTrace V4 M2D-CLAP 2025 - Choisir les morceaux'; $d.Filter='Audio (*.wav;*.mp3)|*.wav;*.mp3'; $d.Multiselect=$true; if($d.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK){[System.IO.File]::WriteAllLines($env:LIST,$d.FileNames)}"

if not exist "%LIST%" (
  echo [INFO] Aucun fichier selectionne.
  timeout /t 2 /nobreak >nul
  exit /b 0
)

echo.
echo [OK] Selection recue :
for /f "usebackq delims=" %%F in ("%LIST%") do echo      %%F
echo.
echo [INFO] Benchmark M2D-CLAP 2025 en cours...
echo [INFO] Chaque morceau = 5 fenetres deterministes EXACTES de 10 secondes a 16 kHz.
echo [INFO] Le TXT n'est JAMAIS utilise pour l'inference.
echo [INFO] La verite benchmark n'est chargee qu'APRES l'inference des morceaux selectionnes.
echo [INFO] Licence upstream custom : Candidate F reste LAB ONLY.
echo [INFO] Cette fenetre RESTERA OUVERTE en cas d'erreur.
echo [INFO] Log permanent : model_lab\results\m2d-clap-2025-last-run.log
echo.

"%LABPY%" "%LAUNCHER%" --engine-label "M2D-CLAP 2025" --runner "%SCRIPT%" --file-list "%LIST%" --log "%LOG%" --error-log "%ERRLOG%"
set "RC=%ERRORLEVEL%"

if not "%RC%"=="0" (
  echo.
  echo ============================================================
  echo  [ERREUR] BENCHMARK M2D-CLAP 2025 ECHOUE - CODE %RC%
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
  echo Envoie-moi m2d-clap-2025-last-error.txt si ca plante.
  echo Cette fenetre ne se fermera pas toute seule.
  echo.
  pause
  exit /b %RC%
)

echo.
echo ============================================================
echo  [OK] BENCHMARK M2D-CLAP 2025 TERMINE
echo ============================================================
echo.
echo Resultats : %RESULTS%
start "" "%RESULTS%"
pause
exit /b 0
