# Script to build XML Watcher executable locally on Windows

param(
    [switch]$Clean = $false
)

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

Write-ColorOutput Green "XML Watcher Service - Build Executable"
Write-ColorOutput Green "======================================"

# Change to project directory
Set-Location $ProjectDir

# Check if virtual environment exists
if (!(Test-Path "venv")) {
    Write-ColorOutput Yellow "Virtual environment not found. Creating one..."
    python -m venv venv
}

# Activate virtual environment
Write-ColorOutput Yellow "Activating virtual environment..."
& ".\venv\Scripts\Activate.ps1"

# Install/upgrade PyInstaller
Write-ColorOutput Yellow "Installing PyInstaller..."
python -m pip install --upgrade pyinstaller

# Install project dependencies
Write-ColorOutput Yellow "Installing project dependencies..."
pip install -r requirements.txt

# Clean previous build if requested
if ($Clean -or (Test-Path "build") -or (Test-Path "dist")) {
    Write-ColorOutput Yellow "Cleaning previous build..."
    Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue
}

# Build executable
Write-ColorOutput Yellow "Building executable..."
pyinstaller xml-watcher.spec --clean

# Check if build was successful
if (Test-Path "dist\xml-watcher.exe") {
    Write-ColorOutput Green "Build successful!"
    Write-ColorOutput White "Executable location: $ProjectDir\dist\"
    
    # List built files
    Write-ColorOutput Yellow "`nBuilt files:"
    Get-ChildItem -Path "dist" | Format-Table Name, Length, LastWriteTime
} else {
    Write-ColorOutput Red "Build failed!"
    exit 1
}

# Test the executable
Write-ColorOutput Yellow "`nTesting executable..."
& ".\dist\xml-watcher.exe" --version

Write-ColorOutput Green "`nBuild complete!"

# Option to copy to a specific location
Write-ColorOutput Yellow "`nWould you like to copy the executable to a specific location?"
$response = Read-Host "Copy executable? (y/N)"
if ($response -eq 'y' -or $response -eq 'Y') {
    $destination = Read-Host "Enter destination path"
    if (Test-Path $destination) {
        Copy-Item "dist\xml-watcher.exe" -Destination $destination -Force
        Copy-Item "dist\config" -Destination $destination -Recurse -Force
        Write-ColorOutput Green "Copied to $destination"
    } else {
        Write-ColorOutput Red "Destination path does not exist"
    }
}
