#!/bin/bash
# Helper script to load environment variables from .env file

ENV_FILE="$(dirname "$0")/../.env"

if [ ! -f "$ENV_FILE" ]; then
    echo "Error: .env file not found at $ENV_FILE"
    exit 1
fi

# Source the .env file
export $(grep -v '^#' "$ENV_FILE" | xargs)

# Calculate derived paths
export PROJECT_ROOT="$BASE_PATH/networkingAgent"

# Check for .wenv first (preferred as it has packages)
if [ -f "$BASE_PATH/.wenv/bin/python" ]; then
    export VENV_PATH="$BASE_PATH/.wenv"
    export PYTHON_EXE="$VENV_PATH/bin/python"
elif [ -f "$PROJECT_ROOT/.venv/bin/python" ]; then
    export VENV_PATH="$PROJECT_ROOT/.venv"
    export PYTHON_EXE="$VENV_PATH/bin/python"
else
    # Fallback to system python
    export PYTHON_EXE="python3"
fi

# Export to parent shell
echo "Environment loaded:"
echo "  BASE_PATH=$BASE_PATH"
echo "  PROJECT_ROOT=$PROJECT_ROOT"
echo "  PYTHON_EXE=$PYTHON_EXE"
