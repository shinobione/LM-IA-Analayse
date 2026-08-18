@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SonicTrace V4 Model Lab - MOSS-Music Candidate G0 PREFLIGHT

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RESULTS=%LAB%\results"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

if not exist "%RESULTS%" mkdir "%RESULTS%" >nul 2>&1

for /f "tokens=1-4 delims=/-. " %%a in ("%date%") do set "DATEPART=%%d%%c%%b"
for /f "tokens=1-3 delims=:,. " %%a in ("%time%") do set "TIMEPART=%%a%%b%%c"
set "TIMEPART=%TIMEPART: =0%"
set "REPORT=%RESULTS%\moss-music-g0-preflight-%DATEPART%-%TIMEPART%.txt"

set "GPU_NAME=UNKNOWN"
set "VRAM_TOTAL=0"
set "VRAM_FREE=0"
set "DRIVER=UNKNOWN"
set "DISK_FREE_GIB=0"
set "WSL_STATUS=NOT_FOUND"
set "UV_STATUS=NOT_FOUND"
set "GPU_STATUS=FAIL"
set "DISK_STATUS=FAIL"
set "G0_STATUS=BLOCKED"

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - CANDIDATE G0 PREFLIGHT
 echo  MOSS-Music-8B-Instruct - ZERO MODEL DOWNLOAD
 echo ============================================================
echo.
echo Ce script :
echo   - ne telecharge AUCUN modele
echo   - n'installe AUCUN package
echo   - ne modifie PAS SonicTrace V3 / Catalogue / STUDIO
echo   - mesure uniquement la faisabilite locale RTX 3060 / disque / WSL
 echo.

where nvidia-smi.exe >nul 2>&1
if errorlevel 1 (
  echo [FAIL] nvidia-smi introuvable.
) else (
  for /f "tokens=1-4 delims=," %%A in ('nvidia-smi --query-gpu=name^,memory.total^,memory.free^,driver_version --format=csv^,noheader^,nounits 2^>nul') do (
    if "!GPU_NAME!"=="UNKNOWN" (
      set "GPU_NAME=%%A"
      set "VRAM_TOTAL=%%B"
      set "VRAM_FREE=%%C"
      set "DRIVER=%%D"
    )
  )
  for /f "tokens=*" %%A in ("!GPU_NAME!") do set "GPU_NAME=%%A"
  for /f "tokens=*" %%A in ("!VRAM_TOTAL!") do set "VRAM_TOTAL=%%A"
  for /f "tokens=*" %%A in ("!VRAM_FREE!") do set "VRAM_FREE=%%A"
  for /f "tokens=*" %%A in ("!DRIVER!") do set "DRIVER=%%A"
  echo [OK] GPU    : !GPU_NAME!
  echo [OK] VRAM   : !VRAM_FREE! MiB libres / !VRAM_TOTAL! MiB total
  echo [OK] Driver : !DRIVER!
  if !VRAM_TOTAL! GEQ 12000 set "GPU_STATUS=BORDERLINE_12GB"
)

for /f "usebackq delims=" %%D in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$p=(Get-Item -LiteralPath $env:ROOT).PSDrive; [math]::Round($p.Free/1GB,2)"`) do set "DISK_FREE_GIB=%%D"
echo [INFO] Disque libre sur le volume du repo : !DISK_FREE_GIB! GiB
powershell -NoProfile -ExecutionPolicy Bypass -Command "if([double]$env:DISK_FREE_GIB -ge 30){exit 0}else{exit 1}" >nul 2>&1
if errorlevel 1 (
  set "DISK_STATUS=LOW"
  echo [WARN] Moins de 30 GiB libres : ne pas telecharger le checkpoint BF16.
) else (
  set "DISK_STATUS=OK"
  echo [OK] Marge disque >= 30 GiB.
)

where wsl.exe >nul 2>&1
if errorlevel 1 (
  echo [WARN] WSL introuvable. Le chemin SGLang officiel n'est pas disponible tel quel.
) else (
  set "WSL_STATUS=AVAILABLE"
  echo [OK] WSL present.
  echo ----- WSL VERSION / STATUS -----
  wsl.exe --version 2>nul
  if errorlevel 1 wsl.exe --status 2>nul
  echo -------------------------------
)

call :resolve_uv
if defined UV (
  set "UV_STATUS=AVAILABLE"
  echo [OK] uv : !UV!
) else (
  echo [INFO] uv introuvable actuellement. Aucun install n'est tente par ce preflight.
)

echo.
echo ----- NVIDIA-SMI -----
where nvidia-smi.exe >nul 2>&1 && nvidia-smi.exe
 echo ----------------------
echo.

if /I "!GPU_STATUS!"=="BORDERLINE_12GB" if /I "!DISK_STATUS!"=="OK" set "G0_STATUS=READY_FOR_QUANTIZED_PROOF_ONLY"

(
  echo SONICTRACE V4 MODEL LAB - MOSS-MUSIC CANDIDATE G0 PREFLIGHT
  echo ============================================================
  echo Generated: %date% %time%
  echo Upstream target: OpenMOSS-Team/MOSS-Music-8B-Instruct
  echo Policy: ZERO MODEL DOWNLOAD / ZERO PACKAGE INSTALL
  echo.
  echo GPU_NAME=!GPU_NAME!
  echo VRAM_TOTAL_MIB=!VRAM_TOTAL!
  echo VRAM_FREE_MIB=!VRAM_FREE!
  echo NVIDIA_DRIVER=!DRIVER!
  echo GPU_GATE=!GPU_STATUS!
  echo DISK_FREE_GIB=!DISK_FREE_GIB!
  echo DISK_GATE=!DISK_STATUS!
  echo WSL=!WSL_STATUS!
  echo UV=!UV_STATUS!
  echo.
  echo G0_STATUS=!G0_STATUS!
  echo.
  echo Interpretation:
  echo - BF16/FP16 MOSS-Music 8B is NOT a 12 GB GPU target.
  echo - 8-bit is not considered safe enough for this card.
  echo - Only an isolated 4-bit/quantized proof is eligible for G1.
  echo - G1 must still prove real audio-conditioned inference before READY.
  echo - No SonicTrace V3, Catalogue or STUDIO integration is authorized here.
) > "%REPORT%"

echo ============================================================
echo  G0 RESULTAT : !G0_STATUS!
 echo ============================================================
echo.
if /I "!G0_STATUS!"=="READY_FOR_QUANTIZED_PROOF_ONLY" (
  echo [OK] La machine peut passer a une ETUDE G1 4-bit isolee.
  echo [IMPORTANT] Cela ne signifie PAS que MOSS-Music tiendra reellement en VRAM.
) else (
  echo [STOP] Ne pas telecharger MOSS-Music pour l'instant.
)
echo.
echo Rapport :
echo   %REPORT%
echo.
pause
exit /b 0

:resolve_uv
set "UV="
for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined UV set "UV=%%I"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"
exit /b 0
