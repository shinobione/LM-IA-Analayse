@echo off
setlocal EnableExtensions EnableDelayedExpansion
cd /d "%~dp0"
title SonicTrace V4 Model Lab - MOSS-Music Candidate G0 PREFLIGHT

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RESULTS=%LAB%\results"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"

if not exist "%RESULTS%" mkdir "%RESULTS%" >nul 2>&1
for /f "usebackq delims=" %%S in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "(Get-Date).ToString('yyyyMMdd-HHmmss')"`) do set "STAMP=%%S"
if not defined STAMP set "STAMP=unknown"
set "REPORT=%RESULTS%\moss-music-g0-preflight-%STAMP%.txt"

set "GPU_NAME=UNKNOWN"
set "VRAM_TOTAL=0"
set "VRAM_FREE=0"
set "DRIVER=UNKNOWN"
set "DISK_FREE_GIB=0"
set "WSL_STATUS=BINARY_MISSING"
set "REBOOT_STATUS=NO_KNOWN_PENDING_REBOOT"
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
echo   - n'active AUCUNE fonctionnalite Windows
echo   - n'invoque PAS WSL ^(evite l'installation automatique Windows^)
echo   - ne modifie PAS SonicTrace V3 / Catalogue / STUDIO
echo   - mesure uniquement la faisabilite locale RTX 3060 / disque
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

rem IMPORTANT: do not invoke wsl.exe here. On Windows 11 a present stub can launch
rem an interactive WSL install/provisioning path, which violates a read-only preflight.
where wsl.exe >nul 2>&1
if errorlevel 1 (
  echo [INFO] Binaire WSL introuvable. Aucun probleme pour G0 : WSL n'est pas un gate.
) else (
  set "WSL_STATUS=BINARY_PRESENT_UNPROBED"
  echo [INFO] wsl.exe est present, mais G0 ne l'invoque volontairement PAS.
  reg query "HKCU\Software\Microsoft\Windows\CurrentVersion\Lxss" >nul 2>&1
  if not errorlevel 1 (
    set "WSL_STATUS=USER_STATE_PRESENT_UNPROBED"
    echo [INFO] Un etat utilisateur WSL existe dans le registre ^(lecture seule^).
  )
)

rem Conservative, read-only reboot detection. A pending reboot can come from WSL
rem provisioning or any other Windows servicing operation; G1 must wait until after it.
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending" >nul 2>&1
if not errorlevel 1 set "REBOOT_STATUS=REQUIRED"
reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired" >nul 2>&1
if not errorlevel 1 set "REBOOT_STATUS=REQUIRED"
if /I "!REBOOT_STATUS!"=="REQUIRED" (
  echo [WARN] Un redemarrage Windows est en attente. G1 doit attendre le reboot.
) else (
  echo [OK] Aucun indicateur standard de reboot Windows en attente.
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
if /I "!G0_STATUS!"=="READY_FOR_QUANTIZED_PROOF_ONLY" if /I "!REBOOT_STATUS!"=="REQUIRED" set "G0_STATUS=READY_FOR_QUANTIZED_PROOF_ONLY_AFTER_REBOOT"

(
  echo SONICTRACE V4 MODEL LAB - MOSS-MUSIC CANDIDATE G0 PREFLIGHT
  echo ============================================================
  echo Generated: %date% %time%
  echo Upstream target: OpenMOSS-Team/MOSS-Music-8B-Instruct
  echo Policy: ZERO MODEL DOWNLOAD / ZERO PACKAGE INSTALL / ZERO OS FEATURE INSTALL
  echo.
  echo GPU_NAME=!GPU_NAME!
  echo VRAM_TOTAL_MIB=!VRAM_TOTAL!
  echo VRAM_FREE_MIB=!VRAM_FREE!
  echo NVIDIA_DRIVER=!DRIVER!
  echo GPU_GATE=!GPU_STATUS!
  echo DISK_FREE_GIB=!DISK_FREE_GIB!
  echo DISK_GATE=!DISK_STATUS!
  echo WSL=!WSL_STATUS!
  echo REBOOT=!REBOOT_STATUS!
  echo UV=!UV_STATUS!
  echo.
  echo G0_STATUS=!G0_STATUS!
  echo.
  echo Interpretation:
  echo - BF16/FP16 MOSS-Music 8B is NOT a 12 GB GPU target.
  echo - 8-bit is not considered safe enough for this card.
  echo - Only an isolated 4-bit/quantized proof is eligible for G1.
  echo - G1 must still prove real audio-conditioned inference before READY.
  echo - If REBOOT=REQUIRED, restart Windows before any G1 action.
  echo - WSL is not invoked and is not a G0 pass/fail gate.
  echo - No SonicTrace V3, Catalogue or STUDIO integration is authorized here.
) > "%REPORT%"

echo ============================================================
echo  G0 RESULTAT : !G0_STATUS!
echo ============================================================
echo.
if /I "!G0_STATUS!"=="READY_FOR_QUANTIZED_PROOF_ONLY" (
  echo [OK] La machine peut passer a une ETUDE G1 4-bit isolee.
  echo [IMPORTANT] Cela ne signifie PAS que MOSS-Music tiendra reellement en VRAM.
) else if /I "!G0_STATUS!"=="READY_FOR_QUANTIZED_PROOF_ONLY_AFTER_REBOOT" (
  echo [OK] Le gate materiel G0 passe, MAIS Windows demande un redemarrage.
  echo [ACTION] Redemarre le PC avant toute tentative G1.
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
