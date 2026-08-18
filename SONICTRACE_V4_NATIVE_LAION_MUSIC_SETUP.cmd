@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title SonicTrace V4 Model Lab - Native LAION CLAP Music SETUP

set "ROOT=%~dp0"
set "LAB=%ROOT%model_lab"
set "RUNTIME=%LAB%\.runtime"
set "VENV=%RUNTIME%\native_laion_music_venv"
set "MODEL_DIR=%RUNTIME%\native_laion_music"
set "CHECKPOINT=%MODEL_DIR%\music_audioset_epoch_15_esc_90.14.pt"
set "HF_HOME=%RUNTIME%\huggingface"
set "PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%USERPROFILE%\.local\bin;%PATH%"
set "PYTHONNOUSERSITE=1"
set "PYTHONUTF8=1"
set "HF_HUB_DISABLE_SYMLINKS_WARNING=1"

if not exist "%RUNTIME%" mkdir "%RUNTIME%" >nul 2>&1
if not exist "%MODEL_DIR%" mkdir "%MODEL_DIR%" >nul 2>&1
if not exist "%HF_HOME%" mkdir "%HF_HOME%" >nul 2>&1

echo.
echo ============================================================
echo  SONICTRACE V4 MODEL LAB - NATIVE LAION CLAP MUSIC
echo  ISOLATED CANDIDATE E - DOES NOT MODIFY V3 OR STUDIO
echo ============================================================
echo.
echo Native package   : laion-clap 1.1.7
echo Audio model      : HTSAT-base ^(non-fusion^)
echo Checkpoint       : music_audioset_epoch_15_esc_90.14.pt
echo Checkpoint SHA   : fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd
echo Audio regime     : 48 kHz - exact 10 second clips - CUDA
echo Code license     : Apache-2.0
echo Weight repo      : lukewys/laion_clap - CC0-1.0 metadata
echo Runtime pins     : Torch 2.4.1 cu118 / TorchVision 0.19.1 / TorchAudio 2.4.1 / Transformers 4.51.3 / NumPy 1.26.4
echo.

echo [1/7] Verification uv...
call :resolve_uv
if not defined UV (
  echo [..] Installation automatique de uv...
  where winget.exe >nul 2>&1
  if errorlevel 1 goto :fail
  winget install --id astral-sh.uv -e --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
  if errorlevel 1 goto :fail
  call :resolve_uv
)
if not defined UV goto :fail
echo [OK] uv : %UV%

echo [2/7] Creation environnement Python 3.10 ISOLE Native LAION...
if not exist "%VENV%\Scripts\python.exe" (
  if exist "%VENV%" rmdir /s /q "%VENV%"
  "%UV%" venv --python 3.10 "%VENV%"
  if errorlevel 1 goto :fail
)
"%VENV%\Scripts\python.exe" --version
if errorlevel 1 goto :fail

echo [3/7] Installation PyTorch CUDA 11.8 coherent...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --upgrade "torch==2.4.1" "torchvision==0.19.1" "torchaudio==2.4.1" --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 goto :fail

echo [4/7] Installation LAION CLAP natif + dependances...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" "laion-clap==1.1.7" "transformers==4.51.3" "numpy==1.26.4" "librosa==0.11.0" "huggingface-hub>=0.30,<1" "hf_xet>=1,<2"
if errorlevel 1 goto :fail

echo [5/7] Re-verrouillage ABI CUDA + NumPy apres resolution des deps...
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --reinstall "torch==2.4.1" "torchvision==0.19.1" "torchaudio==2.4.1" --index-url https://download.pytorch.org/whl/cu118
if errorlevel 1 goto :fail
"%UV%" pip install --python "%VENV%\Scripts\python.exe" --reinstall "numpy==1.26.4"
if errorlevel 1 goto :fail

echo [6/7] Telechargement checkpoint musique natif ^(~2.35 GB^) si necessaire...
if not exist "%CHECKPOINT%" (
  "%VENV%\Scripts\python.exe" -c "from huggingface_hub import hf_hub_download; p=hf_hub_download(repo_id='lukewys/laion_clap',filename='music_audioset_epoch_15_esc_90.14.pt',local_dir=r'%MODEL_DIR%'); print('[OK] checkpoint:',p)"
  if errorlevel 1 goto :fail
) else (
  echo [OK] Checkpoint deja present : %CHECKPOINT%
)

echo [7/7] Verification SHA + CUDA + chargement REEL HTSAT-base + embedding...
"%VENV%\Scripts\python.exe" -c "import hashlib,importlib.metadata as m,numpy as np,torch,torchvision,torchaudio,transformers,laion_clap; p=r'%CHECKPOINT%'; h=hashlib.sha256(); f=open(p,'rb'); [h.update(b) for b in iter(lambda:f.read(8*1024*1024),b'')]; f.close(); assert h.hexdigest()=='fae3e9c087f2909c28a09dc31c8dfcdacbc42ba44c70e972b58c1bd1caf6dedd',h.hexdigest(); assert torch.cuda.is_available(); assert torch.__version__.startswith('2.4.1+cu118'),torch.__version__; assert torchvision.__version__.startswith('0.19.1+cu118'),torchvision.__version__; assert torchaudio.__version__.startswith('2.4.1+cu118'),torchaudio.__version__; assert torch.version.cuda=='11.8',torch.version.cuda; assert transformers.__version__=='4.51.3',transformers.__version__; assert np.__version__=='1.26.4',np.__version__; assert m.version('laion-clap')=='1.1.7'; model=laion_clap.CLAP_Module(enable_fusion=False,device='cuda:0',amodel='HTSAT-base'); model.load_ckpt(p,verbose=False); e=np.asarray(model.get_text_embedding(['This audio is a rock song.','This audio is a classical song.'],use_tensor=False)); assert e.shape[0]==2 and e.shape[1]>0,e.shape; assert np.isfinite(e).all(); assert np.linalg.norm(e[0])>0; print('[OK] GPU:',torch.cuda.get_device_name(0)); print('[OK] Torch',torch.__version__,'TorchVision',torchvision.__version__,'TorchAudio',torchaudio.__version__,'CUDA',torch.version.cuda); print('[OK] Transformers',transformers.__version__,'NumPy',np.__version__,'laion-clap',m.version('laion-clap')); print('[OK] Native HTSAT-base checkpoint loaded + text embedding active',e.shape)"
if errorlevel 1 goto :fail

echo.
echo ============================================================
echo  [OK] NATIVE LAION CLAP MUSIC CANDIDATE E PRET
echo ============================================================
echo.
echo Runtime    : %VENV%
echo Checkpoint : %CHECKPOINT%
echo Policy     : 48 kHz / 5 clips deterministes EXACTS de 10s par morceau
echo License    : Apache-2.0 code / CC0-1.0 weight repository metadata
echo.
echo Ensuite double-clique :
echo   SONICTRACE_V4_NATIVE_LAION_MUSIC_BENCHMARK.cmd
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
echo  [ERREUR] NATIVE LAION MUSIC MODEL LAB SETUP A ECHOUE
echo ============================================================
echo CLaMP3, MuQ-MuLan, Microsoft CLAP, Candidate D, SonicTrace V3 et STUDIO n'ont pas ete modifies.
echo Le runtime Candidate E reste isole dans model_lab\.runtime\native_laion_music_venv.
echo Cette fenetre reste ouverte : envoie-moi le dernier bloc d'erreur.
echo.
pause
exit /b 1
