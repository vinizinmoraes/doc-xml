#!/bin/bash
# Script to download pre-built XML Watcher executable

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REPO_OWNER="yourusername"
REPO_NAME="xml-watcher"
GITHUB_API="https://api.github.com"

echo -e "${GREEN}XML Watcher Service - Download Executable${NC}"
echo "=========================================="

# Detect OS
OS="unknown"
ARCH=$(uname -m)

if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    DOWNLOAD_FILE="xml-watcher-linux.tar.gz"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    DOWNLOAD_FILE="xml-watcher-macos.tar.gz"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    DOWNLOAD_FILE="xml-watcher-windows.zip"
    echo -e "${YELLOW}For Windows, please use download-executable.ps1 instead${NC}"
    exit 1
else
    echo -e "${RED}Unsupported operating system: $OSTYPE${NC}"
    exit 1
fi

echo -e "${GREEN}Detected OS: $OS ($ARCH)${NC}"

# Get the latest release
echo -e "\n${YELLOW}Fetching latest release information...${NC}"
LATEST_RELEASE=$(curl -s "$GITHUB_API/repos/$REPO_OWNER/$REPO_NAME/releases/latest")

if [[ $(echo "$LATEST_RELEASE" | grep -c "Not Found") -gt 0 ]]; then
    echo -e "${RED}No releases found. The repository might be private or releases haven't been created yet.${NC}"
    echo -e "${YELLOW}You can manually download from: https://github.com/$REPO_OWNER/$REPO_NAME/releases${NC}"
    exit 1
fi

# Extract version and download URL
VERSION=$(echo "$LATEST_RELEASE" | grep -o '"tag_name": *"[^"]*"' | sed 's/"tag_name": *"//' | sed 's/"//')
DOWNLOAD_URL=$(echo "$LATEST_RELEASE" | grep -o "\"browser_download_url\": *\"[^\"]*$DOWNLOAD_FILE\"" | sed 's/"browser_download_url": *"//' | sed 's/"//')

if [[ -z "$DOWNLOAD_URL" ]]; then
    echo -e "${RED}Could not find download URL for $DOWNLOAD_FILE${NC}"
    echo -e "${YELLOW}Please download manually from: https://github.com/$REPO_OWNER/$REPO_NAME/releases${NC}"
    exit 1
fi

echo -e "${GREEN}Latest version: $VERSION${NC}"

# Create directory
INSTALL_DIR="xml-watcher-$VERSION"
if [[ -d "$INSTALL_DIR" ]]; then
    echo -e "${YELLOW}Directory $INSTALL_DIR already exists.${NC}"
    read -p "Do you want to overwrite it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
    rm -rf "$INSTALL_DIR"
fi

mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Download the file
echo -e "\n${YELLOW}Downloading $DOWNLOAD_FILE...${NC}"
curl -L -o "$DOWNLOAD_FILE" "$DOWNLOAD_URL"

# Extract the archive
echo -e "\n${YELLOW}Extracting archive...${NC}"
if [[ "$OS" == "linux" ]] || [[ "$OS" == "macos" ]]; then
    tar -xzf "$DOWNLOAD_FILE"
    rm "$DOWNLOAD_FILE"
    
    # Make executable
    chmod +x xml-watcher
fi

# Copy example config if it doesn't exist
if [[ ! -f "config/config.yaml" ]] && [[ -f "config/config.yaml.example" ]]; then
    echo -e "\n${YELLOW}Creating configuration file...${NC}"
    cp config/config.yaml.example config/config.yaml
fi

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "\nInstalled in: $(pwd)"
echo -e "\nTo run the service:"
echo -e "  ${YELLOW}cd $INSTALL_DIR${NC}"
echo -e "  ${YELLOW}./xml-watcher${NC}"
echo -e "\n${RED}Don't forget to edit config/config.yaml before starting!${NC}"

# Create symlink option
echo -e "\n${YELLOW}Would you like to create a symlink in /usr/local/bin? (requires sudo)${NC}"
read -p "Create symlink? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    FULL_PATH="$(pwd)/xml-watcher"
    sudo ln -sf "$FULL_PATH" /usr/local/bin/xml-watcher
    echo -e "${GREEN}Symlink created. You can now run 'xml-watcher' from anywhere.${NC}"
fi
