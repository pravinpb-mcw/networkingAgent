# 🎯 Complete System Checklist

Use this checklist to verify everything is set up correctly.

## ✅ Installation & Setup

### Python Environment
- [ ] Python 3.11+ installed (`python --version`)
- [ ] Virtual environment created (`.wenv` or `.venv`)
- [ ] Virtual environment activated
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] No import errors when running `python -c "import phoenix; import langchain"`)

### Node.js & React
- [ ] Node.js 18+ installed (`node --version`)
- [ ] NPM packages installed (`cd react_dashboard && npm install`)
- [ ] React dashboard builds (`npm run build`)
- [ ] `dist/` folder created with built files

### Configuration
- [ ] `.env` file created in project root
- [ ] `ANTHROPIC_API_KEY` set in `.env`
- [ ] `ANTHROPIC_BASE_URL` set in `.env`
- [ ] BASE_PATH auto-detects (or manually set if needed)

## ✅ File Structure

### Required Directories
- [ ] `agents/` exists with 3 agent files
- [ ] `dashboard/backend/` has `main.py`
- [ ] `react_dashboard/src/` has all pages
- [ ] `phoenix/` has `server.py` and `validators/`
- [ ] `scripts/` has `auto_risk_score_updater.py`
- [ ] `server/` has `meraki_server.py`
- [ ] `mock_data/` has `comprehensive_api_data.json`

### Generated Directories (Auto-created)
- [ ] `agent_data/logs/` for log files
- [ ] `.phoenix_data/` for Phoenix database
- [ ] `react_dashboard/dist/` after build

## ✅ System Components

### Backend API
- [ ] Starts without errors: `python -m uvicorn main:app --host 0.0.0.0 --port 8000`
- [ ] Accessible at http://localhost:8000
- [ ] API docs available at http://localhost:8000/docs
- [ ] No hardcoded paths (all dynamic detection)

### React Dashboard  
- [ ] Served by backend at http://localhost:8000
- [ ] All tabs load (Dashboard, AI Analysis, Controls, Phoenix)
- [ ] No console errors in browser
- [ ] Charts render correctly

### Phoenix Observability
- [ ] Starts with `--auto-eval --eval-interval 10`
- [ ] Accessible at http://localhost:6006
- [ ] Database created at `phoenix/.phoenix_data/phoenix_traces.db`
- [ ] Auto-evaluation runs every 10 seconds

### AI Agents
- [ ] Agent 1 (Risk Calculation) uses correct Python path
- [ ] Agent 2 (Nearest AP) uses correct Python path  
- [ ] Agent 3 (Failover Suggestions) runs without MCP errors
- [ ] Risk Updater runs continuously
- [ ] All log files created in `agent_data/logs/`

## ✅ Functionality Tests

### Dashboard Operations
- [ ] Click "Connect Agents" → all agents start
- [ ] Status shows "Connected" after 10-15 seconds
- [ ] Risk scores display in dashboard
- [ ] AP cards show correct data
- [ ] Click "Disconnect Agents" → all agents stop

### Agent Logs
- [ ] Controls tab → Agent Logs shows 5 logs
- [ ] Log files update in real-time
- [ ] Expandable boxes work
- [ ] No error messages in logs (except expected warnings)

### Phoenix Traces
- [ ] Phoenix tab loads iframe
- [ ] Traces appear after agents run
- [ ] Evaluations show 3 metrics:
  - `tool_parameters_complete` (μ ~0.89)
  - `ap_exists_in_topology` (μ 1.00)
  - `risk_math_verification` (μ 1.00)
- [ ] No connection errors

### Scenarios
- [ ] Scenario dropdown shows APs
- [ ] Can select "Healthy" scenario
- [ ] Can select "Degraded" scenario
- [ ] Can select "Failed" scenario
- [ ] Network updates reflect changes

## ✅ Code Quality

### No Hardcoded Paths
- [ ] No `E:\network of obserbility` anywhere
- [ ] No `C:\Users\...` paths
- [ ] All paths use Path objects
- [ ] Environment detection works on any machine

### Error Handling
- [ ] Backend handles missing .env gracefully
- [ ] Frontend shows loading states
- [ ] API errors display user-friendly messages
- [ ] Agents retry on connection failures

### Documentation
- [ ] `SETUP.md` exists with full instructions
- [ ] `react_dashboard/DEVELOPMENT.md` explains React setup
- [ ] `CLEANUP.md` lists safe-to-delete files
- [ ] `.gitignore` covers all build artifacts

## ✅ Git & Deployment

### Version Control
- [ ] `.gitignore` includes:
  - `__pycache__/`
  - `node_modules/`
  - `.env`
  - `*.log`
  - `dist/`
  - `.phoenix_data/`
- [ ] No sensitive data in repo
- [ ] All dependencies in `requirements.txt` and `package.json`

### Portability
- [ ] Works on Windows
- [ ] Works on Mac/Linux (with path adjustments)
- [ ] No absolute paths in code
- [ ] Auto-detects venv location

## ✅ Performance

### Resource Usage
- [ ] Backend uses < 200 MB RAM
- [ ] Phoenix uses < 500 MB RAM
- [ ] Each agent uses < 300 MB RAM
- [ ] Total system uses < 2 GB RAM

### Response Times
- [ ] Dashboard loads in < 3 seconds
- [ ] API responses < 500ms
- [ ] Agent startup < 15 seconds
- [ ] Phoenix evaluations run every 10s

## 🐛 Common Issues Fixed

- [x] ~~MCP "Module not found" error~~ → Fixed with correct Python path
- [x] ~~Phoenix port 4317 binding error~~ → Fixed with port checking
- [x] ~~Evaluations not showing~~ → Fixed with correct API
- [x] ~~Hardcoded paths~~ → All paths now dynamic
- [x] ~~Risk updater not starting~~ → Added to subprocess list
- [x] ~~Connect button not working~~ → Fixed Phoenix detection

## 📋 Pre-Deployment Checklist

Before sharing with friend or deploying:
- [ ] Run complete cleanup (`CLEANUP.md`)
- [ ] Rebuild React: `npm run build`
- [ ] Test fresh install in new folder
- [ ] Verify all documentation is up-to-date
- [ ] Remove any test credentials from `.env.example`
- [ ] Test on clean Python environment

## 🎉 Success Criteria

System is ready when:
- ✅ Dashboard loads without errors
- ✅ All 5 agents start successfully  
- ✅ Phoenix shows traces and evaluations
- ✅ No hardcoded paths anywhere
- ✅ Works on friend's laptop with just SETUP.md
- ✅ No "Module not found" or import errors
- ✅ All documentation is accurate

---

**Need Help?** Check:
1. `SETUP.md` - Full installation guide
2. `CLEANUP.md` - Remove unnecessary files
3. `react_dashboard/DEVELOPMENT.md` - React dev guide
4. Logs in `agent_data/logs/` - Debug agent issues
