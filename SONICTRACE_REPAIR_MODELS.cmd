@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace - Repair Core Models

set "ROOT=%~dp0"
set "BACKEND=%~dp0backend"
set "VENV=%~dp0backend\.venv"
set "HF_HOME=%~dp0backend\models\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
set "HF_HUB_DOWNLOAD_TIMEOUT=300"
set "HF_HUB_ETAG_TIMEOUT=30"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

echo.
echo ============================================================
echo  SONICTRACE - REPAIR CORE MODELS
echo ============================================================
echo.
echo This repairs only SonicTrace production model assets:
echo   - LAION CLAP htsat-unfused
echo   - Discogs-EffNet ONNX + metadata
echo.
echo It does NOT install Model Lab candidates and does NOT touch STUDIO.
echo.

if exist "%ROOT%SONICTRACE_UPDATE.cmd" (
  set "SONICTRACE_NO_PAUSE=1"
  call "%ROOT%SONICTRACE_UPDATE.cmd"
  set "SONICTRACE_NO_PAUSE="
  if errorlevel 1 goto :fail
)

if not exist "%VENV%\Scripts\python.exe" (
  echo [INFO] Core Python runtime is missing. Running the official bootstrap first...
  call "%ROOT%LMNotebook_START.cmd"
  if errorlevel 1 goto :fail
)

call :resolve_uv
if not defined UV (
  echo [ERROR] uv is missing. Run SONICTRACE_INSTALL.cmd once, then retry.
  goto :fail
)

echo [1/4] Stopping the current local runtime so the active 90%% request cannot race the repair...
if exist "%ROOT%LMNotebook_STOP.cmd" call "%ROOT%LMNotebook_STOP.cmd"

echo [2/4] Ensuring neural download transport dependencies...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade -r "%BACKEND%\requirements-neural.txt"
if errorlevel 1 goto :fail

echo [3/4] Prefetching and validating production model assets...
"%VENV%\Scripts\python.exe" "%BACKEND%\prefetch_core_models.py"
if errorlevel 1 goto :fail

echo [4/4] Restarting SonicTrace through the canonical launcher...
call "%ROOT%SONICTRACE_START.cmd"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] SONICTRACE CORE MODELS REPAIRED
echo ============================================================
echo.
echo CLAP and Discogs assets are cached and validated before Studio analysis.
echo You can reload STUDIO and launch a fresh analysis now.
echo.
pause
exit /b 0

:resolve_uv
set "UV="
for /f "delims=" %%I in ('where uv.exe 2^>nul') do if not defined UV set "UV=%%I"
if not defined UV if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe" set "UV=%LOCALAPPDATA%\Microsoft\WinGet\Links\uv.exe"
if not defined UV if exist "%LOCALAPPDATA%\Microsoft\WinGet\Packages" for /f "delims=" %%I in ('where /r "%LOCALAPPDATA%\Microsoft\WinGet\Packages" uv.exe 2^>nul') do if not defined UV set "UV=%%I"
exit /b 0

:fail
echo.
echo ============================================================
echo  [ERROR] CORE MODEL REPAIR FAILED
echo ============================================================
echo.
echo Keep this window open and send the final error block.
echo SonicTrace was not declared repaired.
echo.
pause
exit /b 1
