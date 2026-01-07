#!/bin/bash
# Test environment variables loading
cd "$(dirname "$0")/.."

source "$(dirname "$0")/load_env.sh"

echo "================================================================================"
echo "   ENVIRONMENT VARIABLES TEST"
echo "================================================================================"
echo
echo "BASE_PATH: $BASE_PATH"
echo "PROJECT_ROOT: $PROJECT_ROOT"
echo "VENV_PATH: $VENV_PATH"
echo "PYTHON_EXE: $PYTHON_EXE"
echo
echo "Python version:"
"$PYTHON_EXE" --version
echo
echo "Python location:"
which "$PYTHON_EXE"
echo
echo "================================================================================"
