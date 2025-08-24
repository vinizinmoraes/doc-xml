#!/bin/bash
# Installation script for macOS systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}XML Watcher Service - macOS Installation${NC}"
echo "========================================"
echo -e "${YELLOW}Note: You can also download pre-built executables using:${NC}"
echo -e "  ${GREEN}./scripts/download-executable.sh${NC}"
echo ""

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed.${NC}"
    echo -e "${YELLOW}Install Python 3.8+ using Homebrew: brew install python3${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

# Simple version comparison
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
REQUIRED_MAJOR=$(echo $REQUIRED_VERSION | cut -d. -f1)
REQUIRED_MINOR=$(echo $REQUIRED_VERSION | cut -d. -f2)

if [[ $PYTHON_MAJOR -lt $REQUIRED_MAJOR ]] || [[ $PYTHON_MAJOR -eq $REQUIRED_MAJOR && $PYTHON_MINOR -lt $REQUIRED_MINOR ]]; then
    echo -e "${RED}Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION${NC}"
    exit 1
fi

echo -e "${GREEN}Python $PYTHON_VERSION found${NC}"

# Create virtual environment
echo -e "\n${YELLOW}Creating virtual environment...${NC}"
cd "$PROJECT_DIR"
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo -e "\n${YELLOW}Upgrading pip...${NC}"
pip install --upgrade pip

# Install dependencies
echo -e "\n${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Create directories
echo -e "\n${YELLOW}Creating directories...${NC}"
mkdir -p logs
mkdir -p config

# Copy config file if it doesn't exist
if [ ! -f "config/config.yaml" ]; then
    echo -e "\n${YELLOW}Creating configuration file...${NC}"
    cp config/config.yaml.example config/config.yaml
    echo -e "${YELLOW}Please edit config/config.yaml with your settings${NC}"
fi

# Create launchd plist file
echo -e "\n${YELLOW}Creating launchd plist file...${NC}"
PLIST_FILE="$HOME/Library/LaunchAgents/com.xmlwatcher.service.plist"
PLIST_DIR="$HOME/Library/LaunchAgents"

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.xmlwatcher.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PROJECT_DIR/venv/bin/python</string>
        <string>-m</string>
        <string>src.main</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
    </dict>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/xml-watcher-stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/xml-watcher-stderr.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>
</dict>
</plist>
EOF

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "\nTo start the service automatically:"
echo -e "  ${YELLOW}launchctl load $PLIST_FILE${NC}"
echo -e "\nTo stop the service:"
echo -e "  ${YELLOW}launchctl unload $PLIST_FILE${NC}"
echo -e "\nTo check service status:"
echo -e "  ${YELLOW}launchctl list | grep xmlwatcher${NC}"
echo -e "\nTo run manually:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}python -m src.main${NC}"
echo -e "\n${RED}Don't forget to edit config/config.yaml before starting!${NC}"
