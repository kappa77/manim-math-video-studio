<#
.SYNOPSIS
    One-command installer for the manim-math-video agent skill.

.DESCRIPTION
    Installs the skill for the agents found on this machine and prepares one
    shared Python environment at ~/.manim-math-video/venv.

.EXAMPLE
    irm https://raw.githubusercontent.com/kappa77/manim-math-video-studio/main/install.ps1 | iex

.EXAMPLE
    .\install.ps1 -Platform codex -WithLatex

.EXAMPLE
    .\install.ps1 -Platform all -DryRun

.EXAMPLE
    .\install.ps1 -Uninstall
#>
[CmdletBinding()]
param(
    [string] $Repo = $(if ($env:MMS_REPO) { $env:MMS_REPO } else { 'kappa77/manim-math-video-studio' }),
    [string] $Ref = $(if ($env:MMS_REF) { $env:MMS_REF } else { 'main' }),
    [string] $Platform = 'auto',
    [string] $Root,
    [string] $Venv,
    [switch] $WithLatex,
    [switch] $NoDeps,
    [switch] $DryRun,
    [switch] $Uninstall,
    [switch] $VerboseOutput
)

$ErrorActionPreference = 'Stop'

function Fail([string] $Message) {
    Write-Host "`nERROR: $Message" -ForegroundColor Red
    exit 1
}

function Find-Python {
    foreach ($candidate in @('python3.13', 'python3.12', 'python3.11', 'python3.10', 'python3', 'python')) {
        $command = Get-Command $candidate -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        & $command.Source -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return , @($command.Source) }
    }
    $launcher = Get-Command 'py' -ErrorAction SilentlyContinue
    if ($launcher) {
        & $launcher.Source -3 -c "import sys; raise SystemExit(0 if sys.version_info[:2] >= (3, 10) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { return , @($launcher.Source, '-3') }
    }
    return $null
}

function Invoke-Installer {
    param(
        [Parameter(Mandatory)][string[]] $Python,
        [Parameter(Mandatory)][string] $InstallerPath,
        [Parameter(Mandatory)][string] $SourceDir,
        [string[]] $InstallerArgs = @()
    )
    $prefix = @()
    if ($Python.Count -gt 1) { $prefix = $Python[1..($Python.Count - 1)] }
    $all = @($prefix) + @($InstallerPath) + @('--source', $SourceDir) + @($InstallerArgs)
    & $Python[0] @all
}

$python = @(Find-Python)
if (-not $python -or $python.Count -eq 0) {
    Fail 'Python 3.10+ not found. Install it with: winget install --id Python.Python.3.12 -e'
}

$installerArgs = @('--platform', $Platform)
if ($Root) { $installerArgs += @('--root', $Root) }
if ($Venv) { $installerArgs += @('--venv', $Venv) }
if ($WithLatex) { $installerArgs += '--with-latex' }
if ($NoDeps) { $installerArgs += '--no-deps' }
if ($DryRun) { $installerArgs += '--dry-run' }
if ($Uninstall) { $installerArgs += '--uninstall' }
if ($VerboseOutput) { $installerArgs += '--verbose' }

# Running from a checkout: use the local installer and tree.
if ($PSScriptRoot -and (Test-Path (Join-Path $PSScriptRoot 'install.py'))) {
    Invoke-Installer -Python $python -InstallerPath (Join-Path $PSScriptRoot 'install.py') -SourceDir $PSScriptRoot -InstallerArgs $installerArgs
    exit $LASTEXITCODE
}

# Piped install: fetch the repository archive, then run the installer from it.
$work = Join-Path ([System.IO.Path]::GetTempPath()) ('mms-install-' + [guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $work | Out-Null
try {
    $url = "https://codeload.github.com/$Repo/zip/refs/heads/$Ref"
    $archive = Join-Path $work 'repo.zip'
    Write-Host "Fetching $Repo@$Ref"
    try {
        Invoke-WebRequest -Uri $url -OutFile $archive -UseBasicParsing
    } catch {
        Fail "download failed: $url"
    }
    Expand-Archive -Path $archive -DestinationPath $work -Force
    $source = Get-ChildItem -Path $work -Directory |
        Where-Object { Test-Path (Join-Path $_.FullName 'install.py') } |
        Select-Object -First 1
    if (-not $source) { Fail 'unexpected archive layout; please report this issue' }

    Invoke-Installer -Python $python -InstallerPath (Join-Path $source.FullName 'install.py') -SourceDir $source.FullName -InstallerArgs $installerArgs
    exit $LASTEXITCODE
}
finally {
    Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
}
