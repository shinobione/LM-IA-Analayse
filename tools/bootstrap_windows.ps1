param(
    [switch]$NoUpdate,
    [switch]$NoInstall
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root 'backend'
$Logs = Join-Path $Root 'logs'
$RuntimeFile = Join-Path $Root '.lmn-runtime.json'
New-Item -ItemType Directory -Force -Path $Logs | Out-Null
$LogFile = Join-Path $Logs ("launcher-{0}.log" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
Start-Transcript -Path $LogFile -Force | Out-Null

function Step([string]$Text) {
    Write-Host "`n==> $Text" -ForegroundColor Cyan
}

function Good([string]$Text) {
    Write-Host "[OK] $Text" -ForegroundColor Green
}

function Warn([string]$Text) {
    Write-Host "[!] $Text" -ForegroundColor Yellow
}

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user;$env:LOCALAPPDATA\Microsoft\WinGet\Links"
}

function Has([string]$Name) {
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WingetPackage([string]$Id, [string]$Label) {
    if ($NoInstall) { return $false }
    if (-not (Has 'winget')) {
        Warn "$Label manque et winget n'est pas disponible pour l'installer automatiquement."
        return $false
    }

    Step "Installation automatique : $Label"
    try {
        & winget install --id $Id --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity
        Refresh-Path
        return $true
    } catch {
        Warn "Installation automatique de $Label impossible : $($_.Exception.Message)"
        return $false
    }
}

function Resolve-Python {
    if (Has 'python') {
        return @{ exe = (Get-Command python).Source; prefix = @() }
    }
    if (Has 'py') {
        return @{ exe = (Get-Command py).Source; prefix = @('-3') }
    }
    return $null
}

function Run-Python($Py, [string[]]$Args) {
    & $Py.exe @($Py.prefix) @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Python a retourne le code $LASTEXITCODE."
    }
}

function Port-Listening([int]$Port) {
    try {
        return $null -ne (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1)
    } catch {
        return $false
    }
}

function Api-Ready {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
        return $health.status -in @('ok', 'degraded')
    } catch {
        return $false
    }
}

function Create-DesktopShortcut {
    try {
        $desktop = [Environment]::GetFolderPath('Desktop')
        if (-not $desktop) { return }
        $shortcutPath = Join-Path $desktop 'LMNotebook Audio Analyzer.lnk'
        if (Test-Path $shortcutPath) { return }

        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($shortcutPath)
        $shortcut.TargetPath = Join-Path $Root 'LMNotebook_START.cmd'
        $shortcut.WorkingDirectory = $Root
        $shortcut.Description = 'Lancer LMNotebook Neural Audio Analyzer'
        $shortcut.IconLocation = "$env:SystemRoot\System32\imageres.dll,174"
        $shortcut.Save()
        Good 'Raccourci Bureau cree : LMNotebook Audio Analyzer'
    } catch {
        Warn "Raccourci Bureau non cree : $($_.Exception.Message)"
    }
}

try {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor DarkCyan
    Write-Host ' LMNotebook Neural Audio Analyzer - ONE CLICK LAUNCHER' -ForegroundColor Cyan
    Write-Host '============================================================' -ForegroundColor DarkCyan
    Write-Host 'Je verifie, je repare ce qui peut l etre, puis je lance tout.' -ForegroundColor DarkGray

    Set-Location $Root
    Refresh-Path

    Step 'Mise a jour du projet'
    if ((Test-Path (Join-Path $Root '.git')) -and -not $NoUpdate) {
        if (-not (Has 'git')) {
            Install-WingetPackage 'Git.Git' 'Git' | Out-Null
        }
        Refresh-Path
        if (Has 'git') {
            $dirty = (& git status --porcelain 2>$null)
            if ([string]::IsNullOrWhiteSpace(($dirty -join ''))) {
                & git pull --ff-only
                if ($LASTEXITCODE -eq 0) { Good 'Projet GitHub a jour' } else { Warn 'Mise a jour Git ignoree, lancement de la version locale.' }
            } else {
                Warn 'Fichiers locaux modifies : je ne touche pas au Git pour ne rien ecraser.'
            }
        } else {
            Warn 'Git absent : pas de mise a jour automatique cette fois.'
        }
    } else {
        Good 'Mise a jour Git non requise'
    }

    Step 'Verification Python'
    $Py = Resolve-Python
    if (-not $Py) {
        Install-WingetPackage 'Python.Python.3.12' 'Python 3.12' | Out-Null
        Refresh-Path
        $Py = Resolve-Python
    }
    if (-not $Py) {
        throw 'Python manque toujours. Le lanceur a essaye de l installer automatiquement mais Windows ne le voit pas encore. Relance simplement LMNotebook_START.cmd une fois.'
    }
    $pythonVersion = (& $Py.exe @($Py.prefix) --version 2>&1 | Select-Object -First 1)
    Good "Python : $pythonVersion"

    Step 'Verification FFmpeg / ffprobe'
    if (-not (Has 'ffmpeg')) {
        Install-WingetPackage 'Gyan.FFmpeg' 'FFmpeg' | Out-Null
        Refresh-Path
    }
    if (-not (Has 'ffmpeg')) {
        throw 'FFmpeg manque toujours. Le lanceur a tente l installation automatique. Relance le START; si ca bloque encore, envoie-moi simplement le contenu de cette fenetre.'
    }
    if (-not (Has 'ffprobe')) {
        throw 'ffprobe manque alors que FFmpeg est detecte. Envoie-moi cette fenetre et je corrigerai le PATH.'
    }
    $ffVersion = (& ffmpeg -version 2>$null | Select-Object -First 1)
    Good $ffVersion

    Step 'Verification GPU NVIDIA'
    if (Has 'nvidia-smi') {
        $gpuRows = & nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader 2>$null
        if ($LASTEXITCODE -eq 0 -and $gpuRows) {
            foreach ($row in $gpuRows) { Good "GPU : $row" }
        } else {
            Warn 'nvidia-smi existe mais ne repond pas correctement. V2-A fonctionnera quand meme sur CPU.'
        }
    } else {
        Warn 'nvidia-smi non detecte. V2-A peut tourner sur CPU; CUDA sera active plus tard quand le pilote NVIDIA sera visible.'
    }

    Step 'Preparation du backend V2'
    if (-not (Test-Path $Backend)) { throw 'Dossier backend introuvable.' }
    $Venv = Join-Path $Backend '.venv'
    $VenvPython = Join-Path $Venv 'Scripts\python.exe'
    if (-not (Test-Path $VenvPython)) {
        Write-Host 'Creation de l environnement Python (premiere fois uniquement)...' -ForegroundColor DarkGray
        Run-Python $Py @('-m', 'venv', $Venv)
    }
    & $VenvPython -m pip install --disable-pip-version-check --quiet --upgrade pip
    if ($LASTEXITCODE -ne 0) { throw 'Impossible de mettre pip a jour.' }
    & $VenvPython -m pip install --disable-pip-version-check --quiet -r (Join-Path $Backend 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Impossible d installer les dependances du backend.' }
    Good 'Backend Python pret'

    $EnvFile = Join-Path $Backend '.env'
    $EnvExample = Join-Path $Backend '.env.example'
    if (-not (Test-Path $EnvFile) -and (Test-Path $EnvExample)) {
        Copy-Item $EnvExample $EnvFile
        Good 'Configuration .env creee automatiquement'
    }

    $backendProcess = $null
    $frontendProcess = $null

    Step 'Demarrage Deep Audio V2'
    if (Api-Ready) {
        Good 'API V2 deja active sur le port 8000'
    } elseif (Port-Listening 8000) {
        throw 'Le port 8000 est deja utilise par un autre programme. Ferme ce programme ou lance LMNotebook_STOP.cmd si c est une ancienne instance.'
    } else {
        $backendCommand = "`$Host.UI.RawUI.WindowTitle='LMNotebook V2 API'; Set-Location '$Backend'; & '$VenvPython' -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
        $backendProcess = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-Command',$backendCommand) -PassThru
        Good "API V2 lancee (PID $($backendProcess.Id))"
    }

    Step 'Demarrage de l interface'
    if (Port-Listening 8008) {
        Good 'Frontend deja actif sur le port 8008'
    } else {
        $frontendCommand = "`$Host.UI.RawUI.WindowTitle='LMNotebook Frontend'; Set-Location '$Root'; & '$VenvPython' -m http.server 8008 --bind 127.0.0.1"
        $frontendProcess = Start-Process powershell.exe -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-NoExit','-Command',$frontendCommand) -PassThru
        Good "Frontend lance (PID $($frontendProcess.Id))"
    }

    $runtime = [ordered]@{
        launched_at = (Get-Date).ToString('o')
        backend_pid = if ($backendProcess) { $backendProcess.Id } else { $null }
        frontend_pid = if ($frontendProcess) { $frontendProcess.Id } else { $null }
        api = 'http://127.0.0.1:8000'
        frontend = 'http://127.0.0.1:8008'
    }
    $runtime | ConvertTo-Json | Set-Content -Path $RuntimeFile -Encoding UTF8

    Step 'Attente du moteur'
    $ready = $false
    for ($i = 0; $i -lt 40; $i++) {
        if (Api-Ready) { $ready = $true; break }
        Start-Sleep -Milliseconds 750
    }
    if ($ready) {
        Good 'Deep Audio V2 repond correctement'
    } else {
        Warn 'Le frontend va s ouvrir, mais l API n a pas encore repondu. Regarde la fenetre "LMNotebook V2 API" si besoin.'
    }

    Create-DesktopShortcut

    Step 'Ouverture de LMNotebook'
    Start-Sleep -Milliseconds 600
    Start-Process 'http://127.0.0.1:8008'
    Good 'LMNotebook est lance.'
    Write-Host ''
    Write-Host 'La prochaine fois : double-clic sur LMNotebook_START.cmd (ou le raccourci Bureau).' -ForegroundColor Green
    Write-Host 'Pour tout arreter : double-clic sur LMNotebook_STOP.cmd.' -ForegroundColor DarkGray
    Write-Host "Log : $LogFile" -ForegroundColor DarkGray

    Stop-Transcript | Out-Null
    exit 0
} catch {
    Write-Host ''
    Write-Host 'LMNotebook n a pas pu terminer le demarrage.' -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ''
    Write-Host 'Pas besoin de diagnostiquer toi-meme : copie-moi cette erreur ou envoie un screenshot.' -ForegroundColor Yellow
    Write-Host "Log : $LogFile" -ForegroundColor DarkGray
    try { Stop-Transcript | Out-Null } catch {}
    exit 1
}
