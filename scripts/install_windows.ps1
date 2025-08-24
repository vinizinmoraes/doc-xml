# Installation script for Windows systems
# Run this script in PowerShell as Administrator if you want to install as a service

param(
    [switch]$InstallService = $false
)

# Set error action
$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir

Write-ColorOutput Green "XML Watcher Service - Windows Installation"
Write-ColorOutput Green "=========================================="
Write-ColorOutput Yellow "`nNote: You can also download pre-built executables using:"
Write-ColorOutput Green "  .\scripts\download-executable.ps1"
Write-ColorOutput White ""

# Change to project directory
Set-Location $ProjectDir

# Check Python version
Write-ColorOutput Yellow "`nChecking Python version..."
try {
    $pythonVersion = python --version 2>&1
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 8)) {
            Write-ColorOutput Red "Python 3.8 or higher is required. Found: $pythonVersion"
            Write-ColorOutput Yellow "Download Python from: https://www.python.org/downloads/"
            exit 1
        }
        
        Write-ColorOutput Green "Found $pythonVersion"
    }
} catch {
    Write-ColorOutput Red "Python is not installed or not in PATH"
    Write-ColorOutput Yellow "Download Python from: https://www.python.org/downloads/"
    exit 1
}

# Create virtual environment
Write-ColorOutput Yellow "`nCreating virtual environment..."
python -m venv venv

# Activate virtual environment
Write-ColorOutput Yellow "`nActivating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-ColorOutput Yellow "`nUpgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
Write-ColorOutput Yellow "`nInstalling dependencies..."
pip install -r requirements.txt

# Create directories
Write-ColorOutput Yellow "`nCreating directories..."
New-Item -ItemType Directory -Force -Path "logs" | Out-Null
New-Item -ItemType Directory -Force -Path "config" | Out-Null

# Copy config file if it doesn't exist
if (!(Test-Path "config\config.yaml")) {
    Write-ColorOutput Yellow "`nCreating configuration file..."
    Copy-Item "config\config.yaml.example" "config\config.yaml"
    Write-ColorOutput Yellow "Please edit config\config.yaml with your settings"
}

# Create batch file for easy execution
$batchContent = @"
@echo off
cd /d "$ProjectDir"
call venv\Scripts\activate.bat
python -m src.main %*
"@

Set-Content -Path "xml-watcher.bat" -Value $batchContent

# Create PowerShell script for easy execution
$ps1Content = @"
Set-Location '$ProjectDir'
& '.\venv\Scripts\Activate.ps1'
python -m src.main `$args
"@

Set-Content -Path "xml-watcher.ps1" -Value $ps1Content

Write-ColorOutput Green "`nInstallation complete!"

if ($InstallService) {
    Write-ColorOutput Yellow "`nInstalling as Windows Service requires NSSM (Non-Sucking Service Manager)"
    Write-ColorOutput Yellow "Download NSSM from: https://nssm.cc/download"
    Write-ColorOutput Yellow "`nOnce NSSM is installed, run these commands as Administrator:"
    Write-ColorOutput White "  nssm install XMLWatcher `"$ProjectDir\venv\Scripts\python.exe`" `"-m src.main`""
    Write-ColorOutput White "  nssm set XMLWatcher AppDirectory `"$ProjectDir`""
    Write-ColorOutput White "  nssm set XMLWatcher DisplayName `"XML Watcher Service`""
    Write-ColorOutput White "  nssm set XMLWatcher Description `"Monitors folder for XML files and uploads to API`""
    Write-ColorOutput White "  nssm start XMLWatcher"
} else {
    Write-ColorOutput Yellow "`nTo run the service:"
    Write-ColorOutput White "  Option 1: Double-click xml-watcher.bat"
    Write-ColorOutput White "  Option 2: Run .\xml-watcher.ps1 in PowerShell"
    Write-ColorOutput White "  Option 3: Run 'python -m src.main' with virtual environment activated"
    Write-ColorOutput Yellow "`nTo install as a Windows Service, run this script with -InstallService flag"
}

Write-ColorOutput Red "`nDon't forget to edit config\config.yaml before starting!"
