# 📊 Persistent Traces Database Guide

## ✅ Your Traces Are Now Persistent!

All traces are stored in a **SQLite database** that persists across restarts.

## 📁 Database Location

```
E:\network of obserbility\networkingAgent\.phoenix\phoenix_traces.db
```

This file contains ALL your:
- Agent traces
- LLM calls
- Tool executions  
- Evaluations
- Performance metrics

## 🚀 How to Use Persistent Traces

### Step 1: Start Phoenix Server

Always start Phoenix FIRST before running agents:

```powershell
cd networkingAgent
python phoenix_persistent.py --auto-eval
```

This will:
- ✅ Create/use the persistent database at `.phoenix/phoenix_traces.db`
- ✅ Start dashboard at http://localhost:6006
- ✅ Enable auto-evaluation every 60 seconds
- ✅ Keep all traces even after restart

### Step 2: Run Your Agents

In a **separate terminal**, run your agents:

```powershell
cd networkingAgent  
python agents/risk_score_agent.py
```

The agent will:
- ✅ Detect Phoenix is already running
- ✅ Send traces to the existing Phoenix instance
- ✅ NOT start a duplicate Phoenix server
- ✅ All traces saved to persistent database

### Step 3: View Dashboard

Open browser: **http://localhost:6006**

You'll see:
- All current traces
- ALL historical traces from previous runs
- Evaluations with detailed explanations
- Performance metrics over time

## 🔄 Persistence Test

### Test that traces persist:

1. **Start Phoenix**:
   ```powershell
   python phoenix_persistent.py --auto-eval
   ```

2. **Run agent** (creates traces):
   ```powershell
   python agents/risk_score_agent.py
   ```

3. **Check dashboard**: http://localhost:6006 (see traces)

4. **Stop Phoenix**: Press Ctrl+C in Phoenix terminal

5. **Check database size**:
   ```powershell
   Get-Item .phoenix\phoenix_traces.db | Select-Object Length
   ```
   Should show size > 0 bytes

6. **Restart Phoenix**:
   ```powershell
   python phoenix_persistent.py --auto-eval
   ```

7. **Refresh dashboard**: http://localhost:6006
   
8. **✅ ALL previous traces should still be there!**

## 📊 Database Details

### File Structure:
```
networkingAgent/
  .phoenix/
    phoenix_traces.db  ← YOUR PERSISTENT DATABASE
```

### What's Stored:
- **Traces**: Every agent execution
- **Spans**: Individual LLM calls, tool calls
- **Evaluations**: Hallucination detection results
- **Annotations**: Evaluation scores and explanations
- **Metadata**: Timestamps, costs, latency, tokens

### Database Tables:
Phoenix creates ~20+ tables including:
- `traces` - Main trace records
- `spans` - Individual operations
- `trace_annotations` - Evaluation results
- `projects` - Project organization
- And many more...

## 🛠️ Troubleshooting

### Problem: Traces disappear after restart

**Solution**: Make sure you're using `phoenix_persistent.py`, not launching Phoenix from agents

✅ **Correct**:
```powershell
# Terminal 1
python phoenix_persistent.py --auto-eval

# Terminal 2
python agents/risk_score_agent.py
```

❌ **Wrong**:
```powershell
# This creates temporary Phoenix instance
python agents/risk_score_agent.py
```

### Problem: Port 4317 already in use

**Solution**: Only run ONE Phoenix instance. Kill any duplicates:

```powershell
Get-Process python | Where-Object { $_.Path -like "*\.wenv\*" } | Stop-Process -Force
```

Then restart Phoenix properly:
```powershell
python phoenix_persistent.py --auto-eval
```

### Problem: Database is 0 bytes

**Cause**: Agents tried to launch their own Phoenix instance instead of using the persistent one

**Solution**: 
1. Stop all Python processes
2. Delete `.phoenix/phoenix_traces.db`
3. Start Phoenix properly: `python phoenix_persistent.py --auto-eval`
4. Run agents AFTER Phoenix is running

### Problem: Can't see old traces

**Check**:
1. Database file exists and has size > 0:
   ```powershell
   dir .phoenix\phoenix_traces.db
   ```

2. Phoenix is using correct database URL:
   Look for this in startup output:
   ```
   💾 Database URL: sqlite:///E:/network of obserbility/networkingAgent/.phoenix/phoenix_traces.db
   ```

3. Tables exist in database:
   Phoenix should show "Database tables: XX found" during startup

## 💡 Best Practices

### Always Use This Workflow:

1. **Start Phoenix once** at beginning of day:
   ```powershell
   python phoenix_persistent.py --auto-eval
   ```

2. **Leave it running** in background

3. **Run agents as needed** in other terminals:
   ```powershell
   python agents/risk_score_agent.py
   python agents/nearest_ap_agent.py
   # etc.
   ```

4. **All traces accumulate** in the persistent database

5. **Stop Phoenix** only when done for the day:
   - Ctrl+C in Phoenix terminal
   - Database remains intact for next time

### Backup Your Database:

```powershell
# Backup traces database
copy .phoenix\phoenix_traces.db .phoenix\phoenix_traces_backup.db
```

### Export Traces to CSV:

From Python:
```python
from phoenix.session.client import Client

client = Client("http://localhost:6006")
spans_df = client.get_spans_dataframe()
spans_df.to_csv("all_traces.csv")
```

## 📈 Database Growth

Expected database growth:
- **Per agent run**: ~100-500 KB
- **Per day** (10 agent runs): ~1-5 MB  
- **Per week**: ~10-30 MB
- **Per month**: ~50-150 MB

The database auto-manages size and performance.

---

**🎉 Your traces are now fully persistent and will survive restarts!**

All historical data remains available in the Phoenix dashboard forever (or until you delete the database file).
