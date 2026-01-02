#!/usr/bin/env python3
"""
Test script to verify .env configuration is working correctly
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 80)
print("   TESTING .ENV CONFIGURATION (Python)")
print("=" * 80)
print()

# Get environment variables
base_path = os.getenv('BASE_PATH')
venv_path = os.getenv('VENV_PATH')
python_exe = os.getenv('PYTHON_EXE')
project_root = os.getenv('PROJECT_ROOT')

print("Environment Variables:")
print(f"  BASE_PATH = {base_path}")
print(f"  VENV_PATH = {venv_path}")
print(f"  PYTHON_EXE = {python_exe}")
print(f"  PROJECT_ROOT = {project_root}")
print()

# Test path expansion
if base_path and '${' not in str(base_path):
    print("[OK] Variables are properly expanded (no ${...} found)")
else:
    print("[WARNING] Variables may not be expanded correctly")
print()

# Check if paths exist
print("Path Verification:")
if project_root and Path(project_root).exists():
    print(f"  [OK] PROJECT_ROOT exists: {project_root}")
else:
    print(f"  [ERROR] PROJECT_ROOT not found: {project_root}")

if python_exe and Path(python_exe).exists():
    print(f"  [OK] PYTHON_EXE exists: {python_exe}")
else:
    print(f"  [ERROR] PYTHON_EXE not found: {python_exe}")

print()

# Test accessing subdirectories
if project_root:
    agent_data_dir = Path(project_root) / "agent_data"
    if agent_data_dir.exists():
        print(f"  [OK] agent_data directory found")
    else:
        print(f"  [ERROR] agent_data directory not found at {agent_data_dir}")
        
    agents_dir = Path(project_root) / "agents"
    if agents_dir.exists():
        print(f"  [OK] agents directory found")
    else:
        print(f"  [ERROR] agents directory not found at {agents_dir}")

print()
print("=" * 80)
print("Test complete!")
print("=" * 80)
