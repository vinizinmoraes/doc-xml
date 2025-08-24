#!/bin/bash
# Script to build XML Watcher executable locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}XML Watcher Service - Build Executable${NC}"
echo "======================================"

# Change to project directory
cd "$PROJECT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install/upgrade PyInstaller
echo -e "${YELLOW}Installing PyInstaller...${NC}"
pip install --upgrade pyinstaller

# Install project dependencies
echo -e "${YELLOW}Installing project dependencies...${NC}"
pip install -r requirements.txt

# Clean previous build
if [ -d "build" ] || [ -d "dist" ]; then
    echo -e "${YELLOW}Cleaning previous build...${NC}"
    rm -rf build dist
fi

# Build executable
echo -e "${YELLOW}Building executable...${NC}"
pyinstaller xml-watcher.spec --clean

# Check if build was successful
if [ -f "dist/xml-watcher" ] || [ -f "dist/xml-watcher.exe" ]; then
    echo -e "${GREEN}Build successful!${NC}"
    echo -e "Executable location: ${PROJECT_DIR}/dist/"
    
    # List built files
    echo -e "\n${YELLOW}Built files:${NC}"
    ls -la dist/
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# Test the executable
echo -e "\n${YELLOW}Testing executable...${NC}"
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
    ./dist/xml-watcher.exe --version
else
    ./dist/xml-watcher --version
fi

echo -e "\n${GREEN}Build complete!${NC}"
