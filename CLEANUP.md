# Cleanup Guide - Remove Unused Files

This document lists files and directories that can be safely deleted to clean up the project.

## ⚠️ Safe to Delete

### Legacy Directories
These are old versions and references, no longer used:

```bash
# Remove old dashboard implementations
rm -rf legacy/
rm -rf refrence_dashboard/
rm -rf dashboard/frontend/

# Remove old batch files (if using dashboard to start agents)
rm -rf batch/
```

### Build Artifacts & Cache
Always safe to regenerate:

```bash
# Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Node.js
rm -rf node_modules/
rm -rf react_dashboard/node_modules/
rm -rf react_dashboard/dist/

# Phoenix data (careful - loses history!)
rm -rf .phoenix/
rm -rf phoenix/.phoenix_data/

# Logs
rm -rf agent_data/logs/
```

### Documentation Drafts
```bash
rm -rf doc/  # If these are outdated drafts
# Keep: docs/, README.md, SETUP.md
```

## 🔒 Keep These

### Essential Directories
- `agents/` - AI agent code
- `dashboard/backend/` - FastAPI server
- `react_dashboard/` - Main UI
- `phoenix/` - Observability
- `core/` - Shared utilities
- `server/` - MCP server
- `scripts/` - Utility scripts
- `eval/` - Evaluation logic
- `mock_data/` - Sample data
- `policies/` - Network policies
- `scenarios/` - Test scenarios

### Essential Files
- `.env` - Environment configuration
- `.gitignore` - Git rules
- `requirements.txt` - Python deps
- `pyproject.toml` - Python project config
- `README.md` - Project overview
- `SETUP.md` - Setup instructions

## 🧹 Complete Cleanup Script

### Windows (PowerShell)
```powershell
# Navigate to project root
cd E:\network of obserbility\networkingAgent

# Remove legacy code
Remove-Item -Recurse -Force legacy
Remove-Item -Recurse -Force refrence_dashboard
Remove-Item -Recurse -Force dashboard\frontend

# Remove build artifacts
Get-ChildItem -Path . -Directory -Recurse -Filter __pycache__ | Remove-Item -Recurse -Force
Get-ChildItem -Path . -File -Recurse -Filter *.pyc | Remove-Item -Force

# Remove node_modules (will be reinstalled)
Remove-Item -Recurse -Force react_dashboard\node_modules -ErrorAction SilentlyContinue

# Remove old logs
Remove-Item -Recurse -Force agent_data\logs -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path agent_data\logs -Force

Write-Host "✅ Cleanup complete!"
```

### Mac/Linux (Bash)
```bash
# Navigate to project root
cd ~/networkingAgent

# Remove legacy code
rm -rf legacy/
rm -rf refrence_dashboard/
rm -rf dashboard/frontend/

# Remove build artifacts
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Remove node_modules
rm -rf react_dashboard/node_modules/

# Remove old logs
rm -rf agent_data/logs/
mkdir -p agent_data/logs/

echo "✅ Cleanup complete!"
```

## 📊 Space Savings

Typical space saved:
- `legacy/` + `refrence_dashboard/` + `dashboard/frontend/`: ~5-10 MB
- `__pycache__/`: ~20-50 MB
- `node_modules/`: ~500-800 MB
- `.phoenix/`: ~10-100 MB (depends on usage)
- `logs/`: ~1-50 MB (depends on usage)

**Total:** ~500 MB - 1 GB

## 🔄 After Cleanup

### Rebuild React
```bash
cd react_dashboard
npm install
npm run build
```

### Verify System Works
```bash
# Start backend
cd dashboard/backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Test in browser
# http://localhost:8000
```

## 📝 Note

- Always commit your changes before doing major cleanup
- Keep backups of `.env` file
- The `agent_data/` directory stores runtime data - only delete logs, not JSON files

## ✅ Checklist After Cleanup

- [ ] React dashboard builds successfully
- [ ] Backend starts without errors
- [ ] Agents can connect
- [ ] No import errors
- [ ] All pages load correctly
- [ ] Phoenix traces work

---

**Need to undo?** If you accidentally delete something important, restore from Git:
```bash
git checkout -- <deleted-file-or-directory>
```
