#!/bin/bash
# Quick Setup Script for Linux
# Run this script after cloning the repository

set -e  # Exit on error

echo "================================================================================"
echo "   Network Observability Agent - Linux Quick Setup"
echo "================================================================================"
echo

# Get the project directory
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "Step 1: Checking prerequisites..."
echo

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✓ Python found: $PYTHON_VERSION"
else
    echo "   ✗ Python 3 not found. Please install Python 3.9 or higher."
    exit 1
fi

# Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "   ✓ Node.js found: $NODE_VERSION"
else
    echo "   ✗ Node.js not found. Please install Node.js 18 or higher."
    exit 1
fi

# Check npm
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "   ✓ npm found: $NPM_VERSION"
else
    echo "   ✗ npm not found. Please install npm."
    exit 1
fi

echo
echo "Step 2: Creating Python virtual environment..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "   ✓ Virtual environment created"
else
    echo "   ○ Virtual environment already exists"
fi

echo
echo "Step 3: Activating virtual environment and installing Python dependencies..."
source .venv/bin/activate
pip install --upgrade pip > /dev/null
pip install -r requirements.txt
echo "   ✓ Python dependencies installed"

echo
echo "Step 4: Installing Node.js dependencies for dashboard..."
cd react_dashboard
if [ ! -d "node_modules" ]; then
    npm install
    echo "   ✓ Node dependencies installed"
else
    echo "   ○ Node dependencies already installed"
fi
cd ..

echo
echo "Step 5: Installing backend dependencies..."
if [ -f "dashboard/backend/requirements.txt" ]; then
    pip install -r dashboard/backend/requirements.txt > /dev/null
    echo "   ✓ Backend dependencies installed"
fi

echo
echo "Step 6: Making batch scripts executable..."
cd batch
chmod +x *.sh
cd ..
echo "   ✓ All shell scripts are now executable"

echo
echo "Step 7: Creating .env file..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
BASE_PATH=$(dirname "$PROJECT_DIR")
PHOENIX_HOST=localhost
PHOENIX_PORT=6006
EOF
    echo "   ✓ .env file created"
    echo "   ⚠ Please update BASE_PATH in .env if needed"
else
    echo "   ○ .env file already exists"
fi

echo
echo "Step 8: Creating necessary directories..."
mkdir -p logs agent_data/logs mock_data
echo "   ✓ Directories created"

echo
echo "================================================================================"
echo "   Setup Complete! 🎉"
echo "================================================================================"
echo
echo "You can now start the system:"
echo
echo "   Start everything:         ./batch/start_complete_system.sh"
echo "   Start agents only:        ./batch/start_system.sh"
echo "   Start dashboard only:     ./batch/start_react_dashboard.sh"
echo "   Check agent status:       ./batch/check_agents.sh"
echo "   Stop all services:        ./batch/stop_agents.sh"
echo
echo "Access the dashboard at:    http://localhost:5173"
echo "Access Phoenix at:          http://localhost:6006"
echo "Backend API docs:           http://localhost:8000/docs"
echo
echo "For more information, see:"
echo "   - docs/LINUX_SETUP.md"
echo "   - batch/README.md"
echo "   - README.md"
echo
echo "================================================================================"
