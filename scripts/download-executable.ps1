# Script to download pre-built XML Watcher executable for Windows

param(
    [string]$InstallPath = "$env:USERPROFILE\xml-watcher"
)

# Configuration
$RepoOwner = "yourusername"
$RepoName = "xml-watcher"
$GitHubAPI = "https://api.github.com"

# Colors for output
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

Write-ColorOutput Green "XML Watcher Service - Download Executable for Windows"
Write-ColorOutput Green "===================================================="

# Check if running as administrator
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if ($IsAdmin) {
    Write-ColorOutput Yellow "Running as Administrator"
}

# Set TLS version for GitHub API
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# Get the latest release
Write-ColorOutput Yellow "`nFetching latest release information..."
try {
    $LatestRelease = Invoke-RestMethod -Uri "$GitHubAPI/repos/$RepoOwner/$RepoName/releases/latest" -Method Get
} catch {
    Write-ColorOutput Red "Failed to fetch release information: $_"
    Write-ColorOutput Yellow "You can manually download from: https://github.com/$RepoOwner/$RepoName/releases"
    exit 1
}

# Extract version and download URL
$Version = $LatestRelease.tag_name
$Asset = $LatestRelease.assets | Where-Object { $_.name -eq "xml-watcher-windows.zip" }

if (-not $Asset) {
    Write-ColorOutput Red "Could not find Windows download in the latest release"
    Write-ColorOutput Yellow "Please download manually from: https://github.com/$RepoOwner/$RepoName/releases"
    exit 1
}

$DownloadUrl = $Asset.browser_download_url
Write-ColorOutput Green "Latest version: $Version"

# Create installation directory
$InstallDir = Join-Path $InstallPath "xml-watcher-$Version"
if (Test-Path $InstallDir) {
    Write-ColorOutput Yellow "Directory $InstallDir already exists."
    $response = Read-Host "Do you want to overwrite it? (y/N)"
    if ($response -ne 'y' -and $response -ne 'Y') {
        exit 1
    }
    Remove-Item -Path $InstallDir -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Set-Location $InstallDir

# Download the file
$ZipFile = "xml-watcher-windows.zip"
Write-ColorOutput Yellow "`nDownloading $ZipFile..."
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $ZipFile -UseBasicParsing
} catch {
    Write-ColorOutput Red "Failed to download: $_"
    exit 1
}

# Extract the archive
Write-ColorOutput Yellow "`nExtracting archive..."
try {
    Expand-Archive -Path $ZipFile -DestinationPath . -Force
    Remove-Item $ZipFile
} catch {
    Write-ColorOutput Red "Failed to extract archive: $_"
    exit 1
}

# Copy example config if it doesn't exist
if ((-not (Test-Path "config\config.yaml")) -and (Test-Path "config\config.yaml.example")) {
    Write-ColorOutput Yellow "`nCreating configuration file..."
    Copy-Item "config\config.yaml.example" "config\config.yaml"
}

Write-ColorOutput Green "`nInstallation complete!"
Write-ColorOutput White "`nInstalled in: $InstallDir"
Write-ColorOutput White "`nTo run the service:"
Write-ColorOutput White "  cd `"$InstallDir`""
Write-ColorOutput White "  .\xml-watcher.exe"
Write-ColorOutput Red "`nDon't forget to edit config\config.yaml before starting!"

# Add to PATH option
Write-ColorOutput Yellow "`nWould you like to add xml-watcher to your PATH?"
$response = Read-Host "Add to PATH? (y/N)"
if ($response -eq 'y' -or $response -eq 'Y') {
    $CurrentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($CurrentPath -notlike "*$InstallDir*") {
        [Environment]::SetEnvironmentVariable("Path", "$CurrentPath;$InstallDir", "User")
        Write-ColorOutput Green "Added to PATH. You can now run 'xml-watcher' from any new terminal window."
    } else {
        Write-ColorOutput Yellow "Already in PATH"
    }
}

# Create Start Menu shortcut option
Write-ColorOutput Yellow "`nWould you like to create a Start Menu shortcut?"
$response = Read-Host "Create shortcut? (y/N)"
if ($response -eq 'y' -or $response -eq 'Y') {
    $WshShell = New-Object -comObject WScript.Shell
    $StartMenu = [Environment]::GetFolderPath("StartMenu")
    $Shortcut = $WshShell.CreateShortcut("$StartMenu\Programs\XML Watcher.lnk")
    $Shortcut.TargetPath = "$InstallDir\xml-watcher.exe"
    $Shortcut.WorkingDirectory = $InstallDir
    $Shortcut.Description = "XML Watcher Service"
    $Shortcut.Save()
    Write-ColorOutput Green "Start Menu shortcut created"
}
