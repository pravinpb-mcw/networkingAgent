# 🚀 Quick Start for New Users

**Welcome!** This guide will get the Network Observability Dashboard running on your laptop in ~15 minutes.

---

## 📦 What You Need to Install

1. **Python 3.11 or newer**
   - Download: https://www.python.org/downloads/
   - ✅ Check "Add Python to PATH" during installation
   - Verify: Open terminal → `python --version`

2. **Node.js 18 or newer**
   - Download: https://nodejs.org/ (get LTS version)
   - Verify: Open terminal → `node --version`

That's it! Just Python and Node.js.

---

## ⚡ 5-Minute Setup

### Step 1: Get the Code
Copy the entire `networkingAgent` folder to your laptop.

### Step 2: Open Terminal
```bash
# Navigate to the folder
cd path/to/networkingAgent

# Example Windows:
cd C:\Users\YourName\Desktop\networkingAgent

# Example Mac/Linux:
cd ~/Desktop/networkingAgent
```

### Step 3: Setup Python
```bash
# Create virtual environment (one-time setup)
python -m venv .wenv

# Activate it
# Windows:
.wenv\Scripts\activate

# Mac/Linux:
source .wenv/bin/activate

# Install Python packages (one-time setup)
pip install -r requirements.txt
```

### Step 4: Setup React Dashboard
```bash
# Go to React folder
cd react_dashboard

# Install packages (one-time setup)
npm install

# Build the dashboard (one-time setup)
npm run build

# Go back to project root
cd ..
```

### Step 5: Create Configuration File
Create a file named `.env` in the `networkingAgent` folder with:

```env
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic
```

*(Replace `your_api_key_here` with the actual API key)*

---

## 🎯 Running the System

### Every Time You Want to Use It:

```bash
# 1. Activate Python environment
.wenv\Scripts\activate  # Windows
source .wenv/bin/activate  # Mac/Linux

# 2. Start the server
cd dashboard/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

### Open Your Browser:
- Go to: **http://localhost:8000**
- Click: **"Connect Agents"** button
- Wait: 10-15 seconds for everything to start
- Done! The dashboard is now live 🎉

### To Stop:
- Press `Ctrl+C` in the terminal
- Or click **"Disconnect Agents"** in the dashboard

---

## 🎨 What You'll See

### Dashboard (Main Page)
- **Risk Wave Chart** - Real-time network risk trends
- **AP Status Cards** - Health of all access points
- **Network Metrics** - Live statistics

### AI Analysis Tab
- **Agent Controls** - Start/stop the AI agents
- **Analysis Results** - AI-generated network recommendations
- **Status Indicator** - Shows when agents are running

### Controls Tab
- **Scenarios** - Simulate network problems
- **Agent Logs** - See what each agent is doing

### Phoenix Traces Tab
- **Observability Dashboard** - Deep trace analysis
- **Evaluation Metrics** - AI validation scores

---

## 🐛 Troubleshooting

### "Python not found"
- Make sure you checked "Add to PATH" during Python installation
- Restart your terminal after installing Python
- Try `python3` instead of `python`

### "Module not found"
- Make sure virtual environment is activated (you should see `(.wenv)` in terminal)
- Run `pip install -r requirements.txt` again

### "Port 8000 already in use"
- Something else is using port 8000
- Windows: `taskkill /F /IM python.exe`
- Mac/Linux: `lsof -ti:8000 | xargs kill -9`

### "npm install fails"
- Delete `node_modules` folder
- Delete `package-lock.json` file
- Run `npm install` again

### Dashboard shows errors
- Check that backend is running (terminal should show "Uvicorn running")
- Make sure `.env` file exists with API keys
- Check browser console (F12) for error messages

---

## 📂 What's What

```
networkingAgent/
├── dashboard/backend/  → FastAPI server (the brain)
├── react_dashboard/    → Web interface (what you see)
├── agents/             → AI agents (3 smart agents)
├── phoenix/            → Observability system
└── .env               → Your configuration (CREATE THIS!)
```

---

## 💡 Pro Tips

1. **Keep terminal open** while using the dashboard
2. **Activate virtual environment** every time you open a new terminal
3. **Check logs** in Controls tab if something seems wrong
4. **Wait 10-15 seconds** after clicking "Connect Agents"

---

## ✅ Is It Working?

You'll know everything is working when:
- ✅ Dashboard loads at http://localhost:8000
- ✅ "Connect Agents" button makes status turn green
- ✅ Risk scores and AP cards show data
- ✅ No error messages in terminal or browser console

---

## 🆘 Need More Help?

Check these files:
- **SETUP.md** - Detailed setup guide
- **CHECKLIST.md** - Verify everything is correct
- **CLEANUP.md** - Remove unnecessary files

Or check the logs:
- `agent_data/logs/` - All agent log files

---

## 🎉 You're Done!

That's it! The system is now running and monitoring your network.

**What it does:**
- Monitors network health 24/7
- Calculates risk scores for each access point
- Suggests failover options if problems are detected
- Shows everything in a beautiful dashboard

Enjoy! 🚀
