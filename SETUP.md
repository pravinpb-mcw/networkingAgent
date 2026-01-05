# Network Observability Agent - Setup Guide

Complete setup instructions for running the Network Observability Dashboard on any machine.

---

## 📋 Prerequisites

### Required Software
1. **Python 3.11+** - [Download](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"
   
2. **Node.js 18+** - [Download](https://nodejs.org/)
   - LTS version recommended
   
3. **Git** (optional) - [Download](https://git-scm.com/)

---

## 🚀 Quick Start (New Machine Setup)

### Step 1: Clone or Copy Project

```bash
# Option A: Clone from Git
git clone <your-repo-url>
cd networkingAgent

# Option B: Copy folder to your machine
# Just copy the entire networkingAgent folder
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python -m venv .wenv

# Activate it (Windows)
.wenv\Scripts\activate

# Activate it (Mac/Linux)
source .wenv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Step 3: Configure Environment Variables

Create a `.env` file in the project root:

```env
# Optional: Only set if project is NOT in default location
# BASE_PATH=C:\your\custom\path

# API Keys (get from your provider)
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic

# Network Configuration (optional)
NETWORK_ID=your_network_id
ORGANIZATION_ID=your_org_id
```

**Note:** The system auto-detects paths, so `BASE_PATH` is optional unless you have a custom setup.

### Step 4: Set Up React Dashboard

```bash
cd react_dashboard

# Install Node.js dependencies
npm install

# Build the dashboard
npm run build
```

### Step 5: Start the System

#### Option A: Start Everything Together (Recommended)

```bash
# From project root
cd dashboard/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

This starts:
- Backend API (port 8000)
- React Dashboard (served by backend)
- When you click "Connect Agents" in the dashboard, it starts:
  - Phoenix Observability (port 6006)
  - All 3 AI Agents
  - Risk Score Updater

#### Option B: Start Components Separately (Development)

**Terminal 1 - Backend:**
```bash
cd dashboard/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

**Terminal 2 - React Dev Server (optional):**
```bash
cd react_dashboard
npm run dev
# Visit http://localhost:5173
```

**Terminal 3 - Phoenix (optional manual start):**
```bash
python phoenix/server.py --auto-eval --eval-interval 10
```

---

## 🌐 Access the Dashboard

1. **Open Browser:** http://localhost:8000
2. **Click "Connect Agents"** in the AI Analysis tab
3. **Wait 10-15 seconds** for all agents to start
4. **View Observability:** http://localhost:6006 (Phoenix)

---

## 📁 Project Structure

```
networkingAgent/
├── .env                          # Environment variables (create this)
├── requirements.txt              # Python dependencies
├── .gitignore                    # Git ignore rules
│
├── agents/                       # AI Agents
│   ├── agent_1_risk_calculation.py
│   ├── agent_2_nearest_ap.py
│   └── agent_3_failover_suggestion.py
│
├── dashboard/
│   └── backend/                  # FastAPI Backend
│       └── main.py               # Main API server
│
├── react_dashboard/              # React Frontend
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── phoenix/                      # Observability Server
│   ├── server.py
│   └── validators/               # Evaluation validators
│
├── scripts/                      # Utility Scripts
│   └── auto_risk_score_updater.py
│
├── mock_data/                    # Sample Network Data
├── agent_data/                   # Runtime Data & Logs
└── server/                       # MCP Server
```

---

## 🔧 Troubleshooting

### Issue: "Module not found"
```bash
# Make sure virtual environment is activated
.wenv\Scripts\activate  # Windows
source .wenv/bin/activate  # Mac/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Port already in use"
```bash
# Kill existing processes (Windows)
taskkill /F /IM python.exe

# Kill specific port (Windows)
netstat -ano | findstr :8000
taskkill /F /PID <PID_NUMBER>

# Mac/Linux
lsof -ti:8000 | xargs kill -9
```

### Issue: "React build fails"
```bash
cd react_dashboard
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: "Agents not starting"
- Check `.env` file exists with API keys
- Check logs in `agent_data/logs/`
- Ensure Python virtual environment is activated
- Verify Python version: `python --version` (should be 3.11+)

---

## 🎯 For Your Friend's Laptop

Send them:
1. **This SETUP.md file**
2. **The entire `networkingAgent` folder**
3. **Instructions to:**
   - Install Python 3.11+
   - Install Node.js 18+
   - Follow Step 2 onwards above

**No paths are hardcoded!** The system auto-detects everything based on file locations.

---

## 🔄 Daily Usage

### Starting the System
```bash
# 1. Activate Python environment
.wenv\Scripts\activate

# 2. Start backend (includes dashboard)
cd dashboard/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Open http://localhost:8000
# 4. Click "Connect Agents" button
```

### Stopping the System
- Press `Ctrl+C` in the terminal running uvicorn
- Or click "Disconnect Agents" in the dashboard

---

## 🧹 Maintenance

### Clean Build Artifacts
```bash
# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Clean React build
cd react_dashboard
rm -rf dist node_modules
npm install
npm run build
```

### Update Dependencies
```bash
# Python
pip install --upgrade -r requirements.txt

# Node.js
cd react_dashboard
npm update
```

---

## 🐛 Debug Mode

### Enable Detailed Logging
```bash
# Backend
cd dashboard/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level debug

# Agents (manual start with verbose output)
python agents/agent_1_risk_calculation.py --continuous 15
```

### Check Agent Logs
```
agent_data/logs/
├── phoenix.log       # Observability server
├── agent1.log        # Risk calculation
├── agent2.log        # Nearest AP
├── agent3.log        # Failover suggestions
└── risk_updater.log  # Risk score updater
```

---

## 📚 Additional Resources

- **Phoenix Dashboard:** http://localhost:6006 (when running)
- **API Documentation:** http://localhost:8000/docs (FastAPI Swagger UI)
- **React Dev Server:** http://localhost:5173 (during development)

---

## ✅ Checklist for New Setup

- [ ] Python 3.11+ installed
- [ ] Node.js 18+ installed
- [ ] Virtual environment created (`.wenv`)
- [ ] Python dependencies installed
- [ ] `.env` file created with API keys
- [ ] React dashboard built (`npm run build`)
- [ ] Backend starts without errors
- [ ] Dashboard accessible at http://localhost:8000
- [ ] Agents connect successfully

---

## 🎉 You're Ready!

The system is now fully set up and ready to monitor your network!
