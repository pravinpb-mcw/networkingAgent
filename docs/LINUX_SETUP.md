# Network Observability Agent - Linux Setup Guide

## 🐧 Linux Installation & Setup

This guide provides instructions for running the Network Observability Agent system on Linux.

### Prerequisites

1. **Python 3.9+**
   ```bash
   python3 --version
   ```

2. **Node.js 18+ and npm**
   ```bash
   node --version
   npm --version
   ```

3. **Git**
   ```bash
   git --version
   ```

### Initial Setup

#### 1. Clone the Repository
```bash
git clone <your-repo-url>
cd networkingAgent
```

#### 2. Create Python Virtual Environment
```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```bash
cat > .env << EOF
BASE_PATH=/home/yourusername/projects
PHOENIX_HOST=localhost
PHOENIX_PORT=6006
EOF
```

Replace `/home/yourusername/projects` with your actual project path.

#### 4. Make Scripts Executable
```bash
cd batch
chmod +x *.sh
# or use the helper script
./make_executable.sh
cd ..
```

#### 5. Install Node Dependencies for Dashboard
```bash
cd react_dashboard
npm install
cd ..
```

### Running the System

#### Option 1: Start Everything (Recommended)
```bash
./batch/start_system.sh
```

This starts:
- Phoenix observability server (port 6006)
- Risk score updater
- Agent 1 - Risk Calculation (port 5001)
- Agent 2 - Nearest AP (port 5002)
- Agent 3 - Failover Orchestrator

#### Option 2: Start Dashboard Only
```bash
./batch/start_react_dashboard.sh
```

This starts:
- Backend API (port 8000)
- React frontend (port 5173)

Access the dashboard at: http://localhost:5173

#### Option 3: Start Individual Components

**Start Phoenix Server:**
```bash
./batch/start_phoenix.sh
```

**Start Individual Agents:**
```bash
./batch/start_agent_1.sh  # Risk Calculation
./batch/start_agent_2.sh  # Nearest AP
./batch/start_agent_3.sh  # Failover Orchestrator
```

**Start Risk Updater:**
```bash
./batch/start_risk_updater.sh
```

### Stopping the System

```bash
./batch/stop_agents.sh
```

This will gracefully stop all running agents and services.

### Restarting the System

```bash
./batch/restart_agents.sh
```

### Troubleshooting

#### Check Environment Variables
```bash
./batch/test_env.sh
```

#### View Logs
Logs are saved in the `logs/` directory:
```bash
tail -f logs/agent1.log
tail -f logs/phoenix.log
tail -f logs/risk_updater.log
```

#### Check Running Processes
```bash
ps aux | grep python | grep agent
ps aux | grep phoenix
```

#### Port Already in Use
If you get "port already in use" errors:
```bash
# Find process using port 6006 (Phoenix)
lsof -i :6006

# Find process using port 5001 (Agent 1)
lsof -i :5001

# Kill the process
kill -9 <PID>
```

### System Requirements

- **RAM**: 2GB minimum, 4GB recommended
- **CPU**: 2 cores minimum
- **Disk**: 1GB free space
- **OS**: Ubuntu 20.04+, Debian 10+, or any modern Linux distribution

### Dependencies Overview

**Python Packages:**
- FastAPI & Uvicorn (API server)
- Phoenix (observability)
- Pydantic (data validation)
- httpx (HTTP client)

**Node Packages:**
- React 18
- Vite (build tool)
- Recharts (visualization)
- Tailwind CSS (styling)

### Differences from Windows

| Feature | Windows | Linux |
|---------|---------|-------|
| Scripts | `.bat` files | `.sh` files |
| Python path | `.venv\Scripts\python.exe` | `.venv/bin/python` |
| Path separator | `\` | `/` |
| Terminal | `cmd` or PowerShell | `bash`, `zsh`, etc. |
| Process management | `taskkill` | `pkill`, `kill` |
| Background jobs | `start` command | `&` operator |

### Running in Production

For production deployment on Linux:

1. **Use systemd services** instead of shell scripts
2. **Set up a reverse proxy** (nginx or Apache)
3. **Enable firewall** rules
4. **Use environment-specific** .env files
5. **Set up logging** with rotation
6. **Monitor with** systemd or supervisor

Example systemd service file (`/etc/systemd/system/noa-agent1.service`):
```ini
[Unit]
Description=Network Observability Agent 1 - Risk Calculation
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/networkingAgent
Environment="PATH=/path/to/networkingAgent/.venv/bin"
ExecStart=/path/to/networkingAgent/.venv/bin/python agents/agent_1_risk_calculation.py --continuous 10
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl enable noa-agent1
sudo systemctl start noa-agent1
sudo systemctl status noa-agent1
```

### Docker Support (Optional)

A Dockerfile will be provided in future updates for containerized deployment.

### Getting Help

- Check logs in `logs/` directory
- Run `./batch/test_env.sh` to verify setup
- Ensure virtual environment is activated
- Check that all ports (5001, 5002, 6006, 8000, 5173) are available

### Quick Reference Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Start system
./batch/start_system.sh

# Start dashboard
./batch/start_react_dashboard.sh

# Stop everything
./batch/stop_agents.sh

# Restart everything
./batch/restart_agents.sh

# View logs
tail -f logs/*.log

# Check processes
ps aux | grep "agent_.*_.*\.py"
```

---

**Note**: All shell scripts must have execute permissions. Run `chmod +x batch/*.sh` if needed.
