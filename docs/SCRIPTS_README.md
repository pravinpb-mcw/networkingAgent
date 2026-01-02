# Quick Start Scripts

Convenience batch files for running the system.

## 📁 Organization

All batch scripts moved to `scripts/batch/` for cleaner root directory.

## 🚀 Main Commands

### Start Phoenix Server
```bash
start_phoenix.bat
```
Starts Phoenix observability dashboard at http://localhost:6006

### Run All Agents
```bash
scripts\batch\run_all_agents.bat
```
Runs Agent 1 → Agent 2 → Agent 3 sequentially

### Individual Agents
```bash
scripts\batch\run_agent1_risk.bat       # Calculate risk scores
scripts\batch\run_agent2_nearest.bat     # Find nearest APs
scripts\batch\run_agent3_failover.bat    # Generate failover suggestions
```

### Support Scripts
```bash
scripts\batch\start_mock_server.bat      # Start MCP mock server
scripts\batch\run_monitor.bat            # Monitor network
scripts\batch\check_status.bat           # Check system status
```

## 📂 Clean Structure

Root directory now contains only:
- `main.py` - Main application entry point
- `start_phoenix.bat` - Phoenix server launcher
- `README.md` - This file
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- All other scripts in `scripts/batch/`
