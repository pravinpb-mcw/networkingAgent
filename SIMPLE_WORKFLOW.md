# 🎯 Simplified Agent System - File-Based Communication

## **How It Works**

Each agent runs **independently** and communicates through JSON files:

### **Agent 1: Risk Score Calculator**
- Calculates risk scores for all APs
- Writes results to: `agent_data/risk_scores.json`
- Run with: `python main.py --agent risk`

### **Agent 2: Nearest AP Recommender**
- Finds nearest failover APs for each AP
- Writes results to: `agent_data/nearest_aps.json`
- Run with: `python main.py --agent nearest`

### **Agent 3: Network Monitor & Reporter**
- Reads JSON files from Agents 1 & 2
- Analyzes and summarizes the data
- Generates professional reports
- Run with: `python main.py --agent monitor`

## **🚀 Quick Start**

### **Option 1: Three Separate Terminals**

**Terminal 1 - Agent 1 (Risk Scores):**
```powershell
cd "e:\network of obserbility\networkingAgent"
python main.py --agent risk
```

**Terminal 2 - Agent 2 (Nearest APs):**
```powershell
cd "e:\network of obserbility\networkingAgent"
python main.py --agent nearest
```

**Terminal 3 - Agent 3 (Monitor/Reporter):**
```powershell
cd "e:\network of obserbility\networkingAgent"
python main.py --agent monitor
```

### **Option 2: Use Batch Files**
1. Double-click `run_agent1_risk.bat`
2. Double-click `run_agent2_nearest.bat`
3. Double-click `run_monitor.bat`

## **📊 Data Flow**

```
┌─────────────┐
│  Agent 1    │──> risk_scores.json
│ Risk Score  │    (AP risk data)
└─────────────┘

┌─────────────┐
│  Agent 2    │──> nearest_aps.json
│ Nearest AP  │    (Failover recommendations)
└─────────────┘

┌─────────────┐         ┌─────────────────┐
│  Agent 3    │ <───────│ risk_scores.json│
│  Monitor    │         │ nearest_aps.json│
│  Reporter   │         └─────────────────┘
└─────────────┘
        │
        ▼
   Reports & Alerts
```

## **✅ Benefits**

- ✅ Each agent runs independently
- ✅ No complex network communication (A2A removed)
- ✅ Simple file-based data sharing
- ✅ Easy to debug - just check the JSON files
- ✅ Can run agents on different schedules
- ✅ Agent 3 works even if Agents 1/2 restart

## **📁 Output Files**

All data is in `agent_data/` directory:
- `risk_scores.json` - From Agent 1
- `nearest_aps.json` - From Agent 2

## **🔍 Troubleshooting**

**Agent 3 shows "No data available"?**
- Make sure Agent 1 and Agent 2 are running
- Check that JSON files exist in `agent_data/`
- Wait a few seconds for agents to calculate first results

**Agents not starting?**
- Ensure you're using the virtual environment Python
- Check that all dependencies are installed
