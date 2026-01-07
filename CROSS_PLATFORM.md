# Network Observability Agent - Cross-Platform Support

## 🖥️ Platform Support

This project now supports **both Windows and Linux**!

### ✅ Windows
- All original `.bat` scripts work as before
- Run from CMD or PowerShell
- Tested on Windows 10/11

### ✅ Linux  
- Complete shell script (`.sh`) equivalents provided
- Tested on Ubuntu 20.04+, Debian 10+
- Should work on any modern Linux distribution

---

## 🚀 Quick Start

### Windows

```cmd
REM Clone and navigate
git clone <repo-url>
cd networkingAgent

REM Create virtual environment
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

REM Install dashboard dependencies
cd react_dashboard
npm install
cd ..

REM Start the system
batch\start_complete_system.bat
```

### Linux

```bash
# Clone and navigate
git clone <repo-url>
cd networkingAgent

# Run automatic setup
chmod +x setup_linux.sh
./setup_linux.sh

# Or manual setup:
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd react_dashboard && npm install && cd ..
cd batch && chmod +x *.sh && cd ..

# Start the system
./batch/start_complete_system.sh
```

---

## 📚 Documentation

- **[Linux Setup Guide](docs/LINUX_SETUP.md)** - Complete Linux installation and usage
- **[Batch Scripts Guide](batch/README.md)** - All available scripts for both platforms
- **[A2A System](docs/A2A_SYSTEM_README.md)** - Agent-to-Agent communication
- **[Main README](README.md)** - Project overview

---

## 🎯 Common Scripts

| Task | Windows | Linux |
|------|---------|-------|
| **Start Everything** | `batch\start_complete_system.bat` | `./batch/start_complete_system.sh` |
| **Start Agents Only** | `batch\start_system.bat` | `./batch/start_system.sh` |
| **Start Dashboard** | `batch\start_react_dashboard.bat` | `./batch/start_react_dashboard.sh` |
| **Check Status** | `batch\check_agents.bat` | `./batch/check_agents.sh` |
| **Stop All** | `batch\stop_agents.bat` | `./batch/stop_agents.sh` |

---

## 🔧 What Works on Linux

✅ **All Core Features:**
- Phoenix observability server
- All 3 agents (Risk, Nearest AP, Failover)
- Agent-to-Agent communication
- Auto risk score updater
- Backend API (FastAPI/Uvicorn)
- React dashboard (Vite)
- All batch script equivalents

✅ **Development Tools:**
- Environment variable loading
- Log management
- Process management
- Status checking

---

## 🐧 Linux-Specific Notes

1. **Make scripts executable first:**
   ```bash
   cd batch
   chmod +x *.sh
   # or use the helper
   ./make_executable.sh
   ```

2. **Python path differences:**
   - Windows: `.venv\Scripts\python.exe`
   - Linux: `.venv/bin/python`

3. **View logs:**
   ```bash
   tail -f logs/*.log
   ```

4. **Check processes:**
   ```bash
   ./batch/check_agents.sh
   ```

---

## 🌐 Service URLs (Both Platforms)

- **Dashboard:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **Phoenix:** http://localhost:6006
- **Agent 1:** http://localhost:5001
- **Agent 2:** http://localhost:5002
- **Agent 3:** http://localhost:5003

---

## 🎉 Quick Setup Summary

### First-Time Linux Users

```bash
# 1. Clone the repository
git clone <repo-url> && cd networkingAgent

# 2. Run the setup script
chmod +x setup_linux.sh && ./setup_linux.sh

# 3. Start everything
./batch/start_complete_system.sh

# 4. Open browser to http://localhost:5173
```

That's it! The system will be running with all agents, backend, and dashboard.

---

## 📖 Need Help?

- See [docs/LINUX_SETUP.md](docs/LINUX_SETUP.md) for detailed Linux instructions
- See [batch/README.md](batch/README.md) for all available scripts
- Check logs in `logs/` directory
- Run status check: `./batch/check_agents.sh`

---

**Cross-platform support means you can develop on any OS!** 🎊
