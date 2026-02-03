#!/bin/bash
#
# Unified AI Project - WSL2 Development Setup Script
# 
# This script sets up a complete development environment for Unified AI Project
# on WSL2 (Windows Subsystem for Linux 2).
#
# Usage:
#   1. Open WSL2 terminal
#   2. Navigate to project: cd /mnt/d/Projects/Unified-AI-Project
#   3. Run: bash scripts/setup-wsl2.sh
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Unified AI Project - WSL2 Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Project root
PROJECT_ROOT="/mnt/d/Projects/Unified-AI-Project"
cd "$PROJECT_ROOT"

# Detect WSL2
if ! grep -q "microsoft" /proc/version 2>/dev/null; then
    echo -e "${YELLOW}Warning: This script is designed for WSL2${NC}"
fi

echo -e "${GREEN}[1/6]${NC} Updating system packages..."
sudo apt update && sudo apt upgrade -y

echo -e "${GREEN}[2/6]${NC} Installing Python 3.12 and dependencies..."
if ! command -v python3.12 &> /dev/null; then
    sudo add-apt-repository ppa:deadsnakes/ppa -y
    sudo apt update
    sudo apt install -y python3.12 python3.12-venv python3.12-dev python3-pip
fi

echo -e "${GREEN}[3/6]${NC} Installing system dependencies..."
sudo apt install -y \
    build-essential \
    cmake \
    git \
    curl \
    wget \
    vim \
    htop \
    unzip \
    zip \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    portaudio19-dev \
    libasound2-dev

echo -e "${GREEN}[4/6]${NC} Creating Python virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists, removing..."
    rm -rf .venv
fi

python3.12 -m venv .venv
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo -e "${GREEN}[5/6]${NC} Installing Python dependencies..."
pip install -r apps/backend/requirements.txt

# Install frontend dependencies
if [ -d "apps/frontend-dashboard" ]; then
    echo "Installing frontend dependencies..."
    cd apps/frontend-dashboard
    npm install
    cd "$PROJECT_ROOT"
fi

echo -e "${GREEN}[6/6]${NC} Configuring Ray (for distributed mode)..."
# Ray is already in requirements.txt, but let's verify
pip install "ray[default]>=2.9.0"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Next steps:"
echo ""
echo -e "  ${YELLOW}1. Start the backend:${NC}"
echo -e "     cd $PROJECT_ROOT/apps/backend"
echo -e "     source ../../.venv/bin/activate"
echo -e "     uvicorn main:app --host 0.0.0.0 --port 8000"
echo ""
echo -e "  ${YELLOW}2. Start the frontend (in a new WSL terminal):${NC}"
echo -e "     cd $PROJECT_ROOT/apps/frontend-dashboard"
echo -e "     npm run dev"
echo ""
echo -e "  ${YELLOW}3. Access the application:${NC}"
echo -e "     Frontend: http://localhost:3000"
echo -e "     Backend:  http://localhost:8000"
echo ""
echo -e "  ${YELLOW}4. For full Ray distributed mode:${NC}"
echo -e "     ray start --head"
echo -e "     # Then restart the backend"
echo ""
echo -e "Happy coding! 🚀"
echo ""
