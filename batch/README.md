# Batch Scripts - Cross-Platform Guide

This directory contains scripts for managing the Network Observability Agent system on both Windows and Linux platforms.

## 📁 Script Overview

### Core System Scripts

| Windows | Linux | Description |
|---------|-------|-------------|
| `start_system.bat` | `start_system.sh` | Start complete system (Phoenix + All Agents + Updater) |
| `start_complete_system.bat` | `start_complete_system.sh` | Start complete system with backend and frontend |
| `start_full_a2a_system.bat` | `start_full_a2a_system.sh` | Start full system with Agent-to-Agent communication |
| `stop_agents.bat` | `stop_agents.sh` | Stop all running services |
| `restart_agents.bat` | `restart_agents.sh` | Restart all services |
| `check_agents.bat` | `check_agents.sh` | Check status of all agents and services |

### Individual Component Scripts

| Windows | Linux | Description |
|---------|-------|-------------|
| `start_agent_1.bat` | `start_agent_1.sh` | Start Agent 1 (Risk Calculation, Port 5001) |
| `start_agent_2.bat` | `start_agent_2.sh` | Start Agent 2 (Nearest AP, Port 5002) |
| `start_agent_3.bat` | `start_agent_3.sh` | Start Agent 3 (Failover, Port 5003) |
| `start_phoenix.bat` | `start_phoenix.sh` | Start Phoenix observability server (Port 6006) |
| `start_risk_updater.bat` | `start_risk_updater.sh` | Start auto risk score updater |
| `start_react_dashboard.bat` | `start_react_dashboard.sh` | Start backend (8000) + frontend (5173) |

### Utility Scripts

| Windows | Linux | Description |
|---------|-------|-------------|
| `load_env.bat` | `load_env.sh` | Load environment variables from .env file |
| `test_env.bat` | `test_env.sh` | Test environment variable configuration |
| - | `make_executable.sh` | Make all shell scripts executable (Linux only) |

## 🚀 Quick Start

### Windows

```cmd
REM Start everything
batch\start_system.bat

REM Or start with dashboard
batch\start_complete_system.bat

REM Stop everything
batch\stop_agents.bat
```

### Linux

```bash
# First time setup - make scripts executable
cd batch
chmod +x *.sh
# or
./make_executable.sh

# Start everything
./batch/start_system.sh

# Or start with dashboard
./batch/start_complete_system.sh

# Stop everything
./batch/stop_agents.sh
```

## 📋 Detailed Usage

### 1. Starting the Complete System

**Windows:**
```cmd
batch\start_system.bat
```

**Linux:**
```bash
./batch/start_system.sh
```

**What it does:**
- Starts Phoenix server on port 6006
- Starts risk score updater (updates every 10s)
- Starts Agent 1 on port 5001
- Starts Agent 2 on port 5002
- Starts Agent 3 on port 5003
- All run in separate terminals/background processes

### 2. Starting with Dashboard

**Windows:**
```cmd
batch\start_complete_system.bat
```

**Linux:**
```bash
./batch/start_complete_system.sh
```

**What it does:**
- Everything from start_system
- Plus Backend API on port 8000
- Plus React Dashboard on port 5173

**Access:**
- Dashboard: http://localhost:5173
- Backend API: http://localhost:8000
- Phoenix: http://localhost:6006

### 3. Starting Individual Agents

**Windows:**
```cmd
batch\start_agent_1.bat
batch\start_agent_2.bat
batch\start_agent_3.bat
```

**Linux:**
```bash
./batch/start_agent_1.sh
./batch/start_agent_2.sh
./batch/start_agent_3.sh
```

### 4. Checking Agent Status

**Windows:**
```cmd
batch\check_agents.bat
```

**Linux:**
```bash
./batch/check_agents.sh
```

Shows:
- Which processes are running
- Which ports are open
- Process IDs
- Log file sizes

### 5. Stopping Everything

**Windows:**
```cmd
batch\stop_agents.bat
```

**Linux:**
```bash
./batch/stop_agents.sh
```

Gracefully stops all running services.

## 🔧 Environment Configuration

All scripts load environment variables from `.env` file in the project root.

**Required .env variables:**

```env
# Windows example
BASE_PATH=E:\network of obserbility
PHOENIX_HOST=localhost
PHOENIX_PORT=6006

# Linux example
BASE_PATH=/home/username/projects
PHOENIX_HOST=localhost
PHOENIX_PORT=6006
```

### Test Your Configuration

**Windows:**
```cmd
batch\test_env.bat
```

**Linux:**
```bash
./batch/test_env.sh
```

## 🐧 Linux-Specific Setup

### First Time Setup

1. **Clone the repository:**
   ```bash
   git clone <repo-url>
   cd networkingAgent
   ```

2. **Create Python virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Install Node dependencies:**
   ```bash
   cd react_dashboard
   npm install
   cd ..
   ```

4. **Make scripts executable:**
   ```bash
   cd batch
   ./make_executable.sh
   cd ..
   ```

5. **Create .env file:**
   ```bash
   cat > .env << EOF
   BASE_PATH=$(dirname $(pwd))
   PHOENIX_HOST=localhost
   PHOENIX_PORT=6006
   EOF
   ```

6. **Run the system:**
   ```bash
   ./batch/start_system.sh
   ```

### Viewing Logs (Linux)

```bash
# View all logs
tail -f logs/*.log

# View specific agent
tail -f logs/agent1.log
tail -f logs/phoenix.log

# View with filtering
grep ERROR logs/*.log
```

### Managing Background Processes (Linux)

```bash
# View running agents
ps aux | grep "agent_.*\.py"

# View process IDs
cat .pids

# Kill specific process
kill -15 <PID>

# Force kill
kill -9 <PID>
```

## 🪟 Windows-Specific Notes

- Scripts run in separate CMD windows for easy monitoring
- Uses `taskkill` for process management
- Window titles help identify each service
- Press Ctrl+C in any window to stop that service

## 🔄 Differences Between Platforms

| Feature | Windows | Linux |
|---------|---------|-------|
| **File Extension** | `.bat` | `.sh` |
| **Python Path** | `.venv\Scripts\python.exe` | `.venv/bin/python` |
| **Path Separator** | `\` | `/` |
| **Background Execution** | `start "Title" cmd /k` | `command &` |
| **Process List** | `tasklist` | `ps aux` |
| **Kill Process** | `taskkill /F /PID` | `kill -9` |
| **Environment Loading** | `call load_env.bat` | `source load_env.sh` |
| **Executable Permission** | Not needed | `chmod +x` required |

## 🐛 Troubleshooting

### Port Already in Use

**Windows:**
```cmd
netstat -ano | findstr :5001
taskkill /F /PID <PID>
```

**Linux:**
```bash
lsof -i :5001
kill -9 <PID>
```

### Python Not Found

**Windows:**
- Check that `.venv\Scripts\python.exe` exists
- Run `batch\test_env.bat` to verify

**Linux:**
```bash
# Check virtual environment
source .venv/bin/activate
which python

# Or test
./batch/test_env.sh
```

### Scripts Not Executable (Linux Only)

```bash
chmod +x batch/*.sh
# or
cd batch && ./make_executable.sh
```

### Environment Variables Not Loading

**Windows:**
- Ensure `.env` file exists in project root
- Check that `BASE_PATH` uses backslashes
- Run `batch\test_env.bat`

**Linux:**
- Ensure `.env` file exists in project root
- Check that `BASE_PATH` uses forward slashes
- Run `./batch/test_env.sh`

### Agent Won't Start

1. **Check logs:**
   - Windows: Look in the CMD window
   - Linux: `tail -f logs/agent1.log`

2. **Check dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Phoenix is running:**
   - Visit http://localhost:6006

4. **Check port availability:**
   - Windows: `netstat -ano | findstr :5001`
   - Linux: `lsof -i :5001`

## 📊 Service Ports Reference

| Service | Port | URL |
|---------|------|-----|
| Phoenix | 6006 | http://localhost:6006 |
| Agent 1 (Risk) | 5001 | http://localhost:5001 |
| Agent 2 (AP) | 5002 | http://localhost:5002 |
| Agent 3 (Failover) | 5003 | http://localhost:5003 |
| Backend API | 8000 | http://localhost:8000 |
| React Dashboard | 5173 | http://localhost:5173 |

## 🚀 Production Deployment

### Linux with systemd

For production environments, use systemd services instead of shell scripts:

```bash
# See docs/LINUX_SETUP.md for complete systemd configuration
sudo systemctl enable noa-agent1
sudo systemctl start noa-agent1
```

### Docker (Coming Soon)

Docker support is planned for containerized deployment across all platforms.

## 📚 Additional Resources

- [Linux Setup Guide](../docs/LINUX_SETUP.md) - Complete Linux installation guide
- [A2A System README](../docs/A2A_SYSTEM_README.md) - Agent-to-Agent communication
- [Main README](../README.md) - Project overview

## 💡 Tips

1. **Always activate virtual environment** before running scripts manually
2. **Check agent status** regularly with `check_agents` script
3. **Monitor logs** for errors and warnings
4. **Use complete_system** for full stack development
5. **Use individual scripts** for debugging specific agents
6. **Stop agents properly** using stop_agents script before system shutdown

---

**Need Help?**
- Check logs in `logs/` directory
- Run `test_env` script to verify configuration
- Ensure all dependencies are installed
- Check that required ports are available
