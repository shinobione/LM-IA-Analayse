@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - CLEANUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "RESULTS=%LAB%\results"
set "HF_HOME=%RUNTIME%\huggingface"

:menu
cls
echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - NETTOYAGE LOCAL
echo ============================================================
echo.
echo Ce script ne touche JAMAIS a :
echo   - backend\.venv ^(SonicTrace V3^)
echo   - Catalogue V2-E
echo   - SHINOBIWAN STUDIO
echo   - model_lab\results ^(rapports benchmark^)
echo.
call :show_total

echo.
echo [1] Nettoyage sur
 echo    Garde MuQ + CLaMP3 + cache partage + resultats
 echo    Supprime Candidate C / D / E / F et leurs gros assets dedies
 echo.
echo [2] Nettoyage fort
 echo    Garde MuQ + cache partage + resultats
 echo    Supprime aussi le runtime / checkout CLaMP3
 echo.
echo [3] Tout nettoyer le Model Lab local
 echo    Supprime TOUS les runtimes, modeles et caches V4 locaux
 echo    Garde uniquement les resultats benchmark
 echo.
echo [4] Afficher le detail de l'espace disque
 echo.
echo [0] Quitter
 echo.
set /p "CHOICE=Choix : "

if "%CHOICE%"=="1" goto safe
if "%CHOICE%"=="2" goto strong
if "%CHOICE%"=="3" goto all
if "%CHOICE%"=="4" goto sizes
if "%CHOICE%"=="0" exit /b 0

goto menu

:safe
cls
echo.
echo === NETTOYAGE SUR ===
echo MuQ et CLaMP3 seront conserves.
echo Les resultats benchmark seront conserves.
echo.
choice /C ON /N /M "Confirmer ? [O/N] "
if errorlevel 2 goto menu

call :remove_dir "%RUNTIME%\msclap_venv" "Candidate C - Microsoft CLAP venv"
call :remove_dir "%RUNTIME%\larger_clap_venv" "Candidate D - HF Larger CLAP venv"
call :remove_dir "%RUNTIME%\native_laion_music_venv" "Candidate E - native LAION venv"
call :remove_dir "%RUNTIME%\native_laion_music" "Candidate E - native LAION assets"
call :remove_dir "%RUNTIME%\m2d_clap_2025_venv" "Candidate F - M2D venv"
call :remove_dir "%RUNTIME%\m2d_clap_2025" "Candidate F - M2D checkpoint/assets"
call :remove_dir "%RUNTIME%\m2d_clap_2025_src" "Candidate F - M2D pinned source"

rem Candidate C/D had large weights in the shared HF cache. These two
rem cache folders are uniquely owned by rejected candidates and can be pruned
rem without deleting MuQ or CLaMP3 model caches.
call :remove_dir "%HF_HOME%\hub\models--microsoft--msclap" "Candidate C - HF cache"
call :remove_dir "%HF_HOME%\hub\models--laion--larger_clap_music" "Candidate D - HF cache"

echo.
echo [OK] Nettoyage sur termine.
call :show_total
pause
goto menu

:strong
cls
echo.
echo === NETTOYAGE FORT ===
echo MuQ sera conserve.
echo CLaMP3 sera supprime localement.
echo Le cache Hugging Face partage est conserve pour ne pas casser MuQ.
echo Les resultats benchmark seront conserves.
echo.
choice /C ON /N /M "Confirmer ? [O/N] "
if errorlevel 2 goto menu

call :remove_dir "%RUNTIME%\venv" "CLaMP3 - venv"
call :remove_dir "%RUNTIME%\clamp3" "CLaMP3 - checkout"
call :remove_dir "%RUNTIME%\msclap_venv" "Candidate C - Microsoft CLAP venv"
call :remove_dir "%RUNTIME%\larger_clap_venv" "Candidate D - HF Larger CLAP venv"
call :remove_dir "%RUNTIME%\native_laion_music_venv" "Candidate E - native LAION venv"
call :remove_dir "%RUNTIME%\native_laion_music" "Candidate E - native LAION assets"
call :remove_dir "%RUNTIME%\m2d_clap_2025_venv" "Candidate F - M2D venv"
call :remove_dir "%RUNTIME%\m2d_clap_2025" "Candidate F - M2D checkpoint/assets"
call :remove_dir "%RUNTIME%\m2d_clap_2025_src" "Candidate F - M2D pinned source"
call :remove_dir "%HF_HOME%\hub\models--microsoft--msclap" "Candidate C - HF cache"
call :remove_dir "%HF_HOME%\hub\models--laion--larger_clap_music" "Candidate D - HF cache"

echo.
echo [OK] Nettoyage fort termine.
echo Le cache HF partage reste volontairement en place pour MuQ.
call :show_total
pause
goto menu

:all
cls
echo.
echo ============================================================
echo  ATTENTION - SUPPRESSION COMPLETE DES MODELES V4 LOCAUX
 echo ============================================================
echo.
echo Ceci supprimera :
echo   - MuQ-MuLan
 echo   - CLaMP3 / MERT
 echo   - Microsoft CLAP
 echo   - LAION candidates
 echo   - M2D-CLAP
 echo   - cache Hugging Face partage du Model Lab
 echo.
echo Ceci NE supprimera PAS model_lab\results.
echo Aucun fichier SonicTrace V3 / Catalogue / STUDIO ne sera touche.
echo.
choice /C ON /N /M "Confirmer la suppression complete ? [O/N] "
if errorlevel 2 goto menu

call :remove_dir "%RUNTIME%" "Tous les runtimes / modeles / caches V4"

echo.
echo [OK] Model Lab local nettoye completement.
echo Les rapports restent dans :
echo   %RESULTS%
call :show_total
pause
goto menu

:sizes
cls
echo.
echo ============================================================
echo  ESPACE DISQUE - MODEL LAB
 echo ============================================================
echo.
if not exist "%RUNTIME%" (
  echo Aucun runtime local present.
  echo.
  pause
  goto menu
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$root=[IO.Path]::GetFullPath($env:RUNTIME);" ^
  "$items=Get-ChildItem -LiteralPath $root -Force -ErrorAction SilentlyContinue;" ^
  "foreach($i in $items){" ^
  "  if($i.PSIsContainer){$b=(Get-ChildItem -LiteralPath $i.FullName -Force -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum}else{$b=$i.Length};" ^
  "  if($null -eq $b){$b=0};" ^
  "  '{0,-34} {1,9:N2} GiB' -f $i.Name,($b/1GB)" ^
  "}"

echo.
call :show_total
pause
goto menu

:show_total
set "RUNTIME=%RUNTIME%"
for /f "usebackq delims=" %%S in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=$env:RUNTIME; if(Test-Path -LiteralPath $p){$b=(Get-ChildItem -LiteralPath $p -Force -Recurse -File -ErrorAction SilentlyContinue ^| Measure-Object Length -Sum).Sum; if($null -eq $b){$b=0}; '{0:N2} GiB' -f ($b/1GB)}else{'0.00 GiB'}"`) do set "TOTAL_SIZE=%%S"
echo Espace utilise par model_lab\.runtime : %TOTAL_SIZE%
exit /b 0

:remove_dir
set "TARGET=%~1"
set "LABEL=%~2"
if not exist "%TARGET%" (
  echo [--] %LABEL% : absent
  exit /b 0
)
echo [..] Suppression : %LABEL%
rmdir /s /q "%TARGET%"
if exist "%TARGET%" (
  echo [ERREUR] Impossible de supprimer : %TARGET%
  exit /b 1
)
echo [OK] %LABEL%
exit /b 0
