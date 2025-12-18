# Phoenix Data Persistence Guide

## Problem: Data Disappears After Restart

By default, Phoenix may use temporary storage. This guide ensures **all traces persist permanently**.

## ✅ Solution Implemented

Phoenix is now configured to use **persistent local storage** in:
```
networkingAgent/.phoenix/phoenix.db
```

## 🔍 How It Works

### Before (Data Lost)
```
Restart Phoenix → Old traces gone ❌
```

### After (Data Persists)
```
Restart Phoenix → Old traces still there ✅
All historical data preserved ✅
```

## 📁 Where Data is Stored

**Location:** `networkingAgent/.phoenix/`

**Files:**
```
.phoenix/
├── phoenix.db          # Main database (ALL TRACES HERE)
├── exports/            # Exported data
├── inferences/         # LLM inference data
└── trace_datasets/     # Trace datasets
```

## ✅ Verify Data Persistence

### Test 1: Check Database File Exists

```bash
# Windows
dir .phoenix\phoenix.db

# Should show the file with a size > 0 KB
```

### Test 2: Restart Phoenix and Check Data

```bash
# 1. Start Phoenix
python phoenix_with_evals.py --auto-eval

# 2. Run agent (creates traces)
python agents\risk_score_agent.py

# 3. Open UI: http://localhost:6006
# You should see traces ✅

# 4. Stop Phoenix (Ctrl+C)

# 5. Restart Phoenix
python phoenix_with_evals.py --auto-eval

# 6. Open UI again: http://localhost:6006
# OLD TRACES STILL THERE ✅
```

## 📊 View Historical Data

### All Traces Available After Restart

**Open Phoenix:** http://localhost:6006

**You'll see:**
- ✅ Today's traces
- ✅ Yesterday's traces  
- ✅ Last week's traces
- ✅ ALL traces ever recorded

**Filter by date:**
- Use date range picker in Phoenix UI
- Filter by project
- Search by trace ID

## 💾 Database Info

**Database Type:** SQLite  
**File:** `.phoenix/phoenix.db`  
**Size:** Grows with data (typically 10-100 MB)  
**Persistent:** YES - survives restarts  

## 🔧 Manual Database Management

### View Database Size
```bash
# Windows PowerShell
Get-Item .phoenix\phoenix.db | Select-Object Name, Length

# Output example:
# Name         Length
# ----         ------
# phoenix.db   15728640  (15 MB)
```

### Backup Database
```bash
# Create backup
copy .phoenix\phoenix.db .phoenix\phoenix_backup.db

# Or with timestamp
copy .phoenix\phoenix.db .phoenix\phoenix_backup_%date:~-4,4%%date:~-10,2%%date:~-7,2%.db
```

### Export Traces to CSV
```python
import phoenix as px
from phoenix.session.client import Client

client = Client(endpoint="http://localhost:6006")
spans_df = client.get_spans_dataframe()

# Export all traces
spans_df.to_csv("all_traces_export.csv", index=False)
print(f"Exported {len(spans_df)} traces")
```

### Clear Old Data (If Needed)
```bash
# Stop Phoenix first!
# Then delete database
del .phoenix\phoenix.db

# Next time Phoenix starts, it creates fresh database
```

## 📈 Data Growth

**Typical sizes:**
- 10 agent runs: ~5 MB
- 100 agent runs: ~20 MB
- 1,000 agent runs: ~150 MB

**Recommendation:** Backup database weekly if running frequently.

## 🚨 Troubleshooting

### "No traces showing after restart"

**Check 1:** Database file exists
```bash
dir .phoenix\phoenix.db
```

**Check 2:** Environment variable set
```python
import os
print(os.environ.get("PHOENIX_SQL_DATABASE_URL"))
# Should show: sqlite:///.phoenix/phoenix.db
```

**Check 3:** Phoenix using correct directory
- Look for startup message:
  ```
  💾 Database: E:\network of obserbility\networkingAgent\.phoenix\phoenix.db
  📚 Loaded existing data
  ```

### "Database locked" error

**Cause:** Phoenix already running or crashed

**Solution:**
1. Stop all Phoenix processes
2. Close Phoenix UI in browser
3. Wait 10 seconds
4. Restart Phoenix

### "Database corrupted"

**Rare issue - Solution:**
```bash
# 1. Stop Phoenix
# 2. Rename corrupted DB
ren .phoenix\phoenix.db phoenix.db.corrupted

# 3. Restart Phoenix (creates new DB)
python phoenix_with_evals.py --auto-eval

# 4. If you need old data, use SQLite recovery tools
```

## 📊 Viewing Old Data

### Phoenix UI Features

**Traces Tab:**
- See all traces sorted by date
- Use filters: `timestamp > "2025-12-01"`
- Group by project/model

**Search:**
- Search by AP serial
- Search by error messages
- Search by risk scores

**Time Range:**
- Last hour
- Last 24 hours
- Last 7 days
- Custom range
- **All time** ✅

## 🎯 Best Practices

1. **Keep Phoenix Running:** Use standalone server for 24/7 availability
2. **Regular Backups:** Backup `.phoenix/` folder weekly
3. **Monitor Size:** Check DB size monthly
4. **Export Important Data:** Export critical traces to CSV
5. **Clean Old Data:** Archive traces older than 3 months if needed

## ✅ Confirmation

After following this guide, you should be able to:

✅ Restart Phoenix and see old traces  
✅ View traces from days/weeks ago  
✅ Search historical data  
✅ Export all traces  
✅ Never lose data on restart  

## 🚀 Quick Test

**Verify persistence now:**

```bash
# Start Phoenix
python phoenix_with_evals.py --auto-eval

# Check for "Loaded existing data" message
# Open http://localhost:6006
# See your old traces ✅
```

**Data is now persistent and safe!** 🎉
