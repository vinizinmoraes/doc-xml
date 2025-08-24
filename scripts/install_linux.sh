#!/bin/bash
# Installation script for Linux systems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${GREEN}XML Watcher Service - Linux Installation${NC}"
echo "========================================"
echo -e "${YELLOW}Note: You can also download pre-built executables using:${NC}"
echo -e "  ${GREEN}./scripts/download-executable.sh${NC}"
echo ""

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}This script should not be run as root!${NC}"
   exit 1
fi

# Check Python version
echo -e "\n${YELLOW}Checking Python version...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [[ $(echo -e "$PYTHON_VERSION\n$REQUIRED_VERSION" | sort -V | head -n1) != "$REQUIRED_VERSION" ]]; then
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

# Create systemd service file
echo -e "\n${YELLOW}Creating systemd service file...${NC}"
SERVICE_FILE="/tmp/xml-watcher.service"

cat > "$SERVICE_FILE" << EOF
[Unit]
Description=XML Watcher Service
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$PROJECT_DIR/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "\n${GREEN}Installation complete!${NC}"
echo -e "\nTo install as a system service, run:"
echo -e "  ${YELLOW}sudo cp $SERVICE_FILE /etc/systemd/system/${NC}"
echo -e "  ${YELLOW}sudo systemctl daemon-reload${NC}"
echo -e "  ${YELLOW}sudo systemctl enable xml-watcher${NC}"
echo -e "  ${YELLOW}sudo systemctl start xml-watcher${NC}"
echo -e "\nTo run manually:"
echo -e "  ${YELLOW}source venv/bin/activate${NC}"
echo -e "  ${YELLOW}python -m src.main${NC}"
echo -e "\n${RED}Don't forget to edit config/config.yaml before starting!${NC}"
