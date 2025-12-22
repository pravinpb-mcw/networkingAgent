# 3-Agent A2A Communication System

## Overview

This system demonstrates **Agent-to-Agent (A2A)** communication between three intelligent agents that work together to monitor network health and suggest failovers.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    A2A COMMUNICATION FLOW                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Agent 1: Risk Score Calculation                            │
│  ├─ Runs continuously (every 10s)                          │
│  ├─ Calculates risk scores for all APs                     │
│  ├─ Stores in: agent_data/risk_scores.json                 │
│  └─ A2A Server (port 5001) ← Provides risk data           │
│                                                             │
│  Agent 2: Nearest AP Finder                                 │
│  ├─ Runs continuously (every 30s)                          │
│  ├─ Finds nearest APs for each AP                          │
│  ├─ Stores in: agent_data/nearest_aps.json                 │
│  └─ A2A Server (port 5002) ← Provides nearest AP data      │
│                                                             │
│  Agent 3: Failover Orchestrator                             │
│  ├─ Runs continuously (every 15s)                          │
│  ├─ Queries Agent 1 via A2A for risk scores                │
│  ├─ Filters APs with risk >= 41 (policy threshold)         │
│  ├─ For failing APs, queries Agent 2 via A2A               │
│  └─ Generates intelligent failover suggestions             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Workflow

### Agent 1: Risk Score Provider
**What it does:**
- Continuously calculates risk scores for all access points
- Stores results in `agent_data/risk_scores.json`
- Runs an A2A server that provides risk data to other agents

**A2A Skills:**
- `get_all_risk_scores` - Returns all risk scores
- `get_at_risk_aps` - Returns APs above a threshold

### Agent 2: Nearest AP Provider
**What it does:**
- Continuously calculates nearest APs for each access point
- Stores results in `agent_data/nearest_aps.json`
- Runs an A2A server that provides nearest AP data to other agents

**A2A Skills:**
- `get_nearest_aps <ap_serial>` - Returns nearest APs for specific AP
- `get_all_nearest_aps` - Returns all nearest AP data

### Agent 3: Intelligent Failover Orchestrator
**What it does:**
1. Queries Agent 1 (via A2A) for current risk scores
2. Identifies APs exceeding threshold (41 from policy)
3. For each failing AP, queries Agent 2 (via A2A) for nearest APs
4. Generates comprehensive failover suggestions with reasoning

**Output:**
- Detailed failover report
- Top 3 failover candidates per failing AP
- Distance, RSSI, and scoring metrics
- Clear recommendations

## Quick Start

### Option 1: Automated Startup (Recommended)
```batch
start_full_a2a_system.bat
```

This starts all 5 components automatically:
1. Agent 1 - Risk Calculation (continuous)
2. Agent 1 - A2A Server (port 5001)
3. Agent 2 - Nearest AP (continuous)
4. Agent 2 - A2A Server (port 5002)
5. Agent 3 - Failover Monitor (A2A client)

### Option 2: Manual Startup

**Terminal 1 - Agent 1 Calculation:**
```batch
.wenv\Scripts\activate
python agents\agent_1_risk_calculation.py --continuous 10
```

**Terminal 2 - Agent 1 A2A Server:**
```batch
.wenv\Scripts\activate
python agents\agent_1_a2a_server.py
```

**Terminal 3 - Agent 2 Calculation:**
```batch
.wenv\Scripts\activate
python agents\agent_2_nearest_ap.py --continuous 30
```

**Terminal 4 - Agent 2 A2A Server:**
```batch
.wenv\Scripts\activate
python agents\agent_2_a2a_server.py
```

**Terminal 5 - Agent 3 Failover Monitor:**
```batch
.wenv\Scripts\activate
python agents\agent_3_failover_a2a.py --continuous 15
```

## Prerequisites

1. **Python Environment:**
   ```batch
   .wenv\Scripts\activate
   ```

2. **Install python-a2a:**
   ```batch
   pip install python-a2a
   ```

3. **Mock Server (if testing):**
   Start the mock Meraki server first in a separate terminal

## Configuration

### Risk Threshold
The failover threshold is defined in `policies/network_policy.json`:
```json
{
  "failover_criteria": {
    "minimum_risk_score_for_failover": 41
  }
}
```

### Agent Intervals
You can customize the check intervals:

```batch
# Agent 1 - check every 10 seconds
python agents\agent_1_risk_calculation.py --continuous 10

# Agent 2 - check every 30 seconds  
python agents\agent_2_nearest_ap.py --continuous 30

# Agent 3 - check every 15 seconds
python agents\agent_3_failover_a2a.py --continuous 15
```

## Testing A2A Communication

### Test Simple A2A:
```batch
python test_a2a_clean.py
```

This runs a simple test with two agents to verify A2A protocol works.

### Verify Agent Communication:
```batch
python scripts\verify_a2a.py
```

This checks if Agent 1 and Agent 2 A2A servers are running and responsive.

## Example Output

When Agent 3 finds failing APs, you'll see:

```
========================================================================
🚨 FAILOVER SUGGESTION REPORT
========================================================================
📅 Timestamp: 2025-12-22T15:30:00
🎯 Threshold: 41
📊 Failing APs: 2
========================================================================

⚠️ **2 AP(s) REQUIRE FAILOVER**

────────────────────────────────────────────────────────────────────────
AP #1: AP-03 (Q2XX-ABCD-1234)
────────────────────────────────────────────────────────────────────────
🔴 Risk Score: 65/100
📊 Classification: Degrading

🎯 FAILOVER CANDIDATES (3 found):

🥇 RANK 1: AP-05 (Q2XX-EFGH-5678)
   Distance: 12.5m
   RSSI: -45dBm
   Score: 95.2
   Same Floor: Yes

💡 RECOMMENDATION:
   → Failover to: AP-05 (Q2XX-EFGH-5678)
   → Distance: 12.5m
   → Expected signal: -45dBm

========================================================================
✅ Report Complete
========================================================================
```

## Files Created

### Core Agents:
- `agents/agent_1_risk_calculation.py` - Risk score calculator (existing)
- `agents/agent_2_nearest_ap.py` - Nearest AP finder (existing)
- `agents/agent_3_failover_a2a.py` - **NEW** Failover orchestrator with A2A

### A2A Servers:
- `agents/agent_1_a2a_server.py` - **NEW** A2A server for Agent 1
- `agents/agent_2_a2a_server.py` - **NEW** A2A server for Agent 2

### Utilities:
- `start_full_a2a_system.bat` - **NEW** Start all agents automatically
- `test_a2a_clean.py` - **NEW** Test A2A protocol

### Data Files:
- `agent_data/risk_scores.json` - Generated by Agent 1
- `agent_data/nearest_aps.json` - Generated by Agent 2

## How It Works

1. **Agent 1** continuously monitors all APs and calculates risk scores based on metrics like latency, jitter, SNR, retransmissions, etc.

2. **Agent 1 A2A Server** reads the risk scores from JSON and serves them via A2A protocol on port 5001.

3. **Agent 2** continuously calculates the nearest APs for each AP based on distance, signal strength, and topology.

4. **Agent 2 A2A Server** reads the nearest AP data from JSON and serves it via A2A protocol on port 5002.

5. **Agent 3** orchestrates failover decisions by:
   - Querying Agent 1 via A2A: "Give me all risk scores"
   - Filtering APs where risk >= 41
   - For each failing AP, querying Agent 2 via A2A: "Give me nearest APs for X"
   - Generating intelligent failover suggestions

## Benefits of A2A

✅ **Real-time Communication** - Agents query each other directly
✅ **No File Polling** - A2A is faster than reading JSON files
✅ **Dynamic Queries** - Can request specific data (e.g., "APs above threshold")
✅ **Scalable** - Easy to add more agents
✅ **Standard Protocol** - Uses Google's A2A specification

## Troubleshooting

### Agent 3 can't connect to Agent 1/2:
- Make sure Agent 1 and 2 A2A servers are running
- Check ports 5001 and 5002 are not blocked
- Verify data files exist in `agent_data/`

### No failing APs found:
- This is normal if all APs are healthy
- Check `agent_data/risk_scores.json` to see actual scores
- Adjust threshold in Agent 3 or policy file

### A2A import error:
```batch
pip install python-a2a
```

## Summary

This system demonstrates a real-world AI agent collaboration pattern where:
- **Agent 1** provides risk analysis
- **Agent 2** provides topology/proximity data  
- **Agent 3** orchestrates intelligent decisions by combining data from both agents

All communication happens via the A2A protocol, making it a clean, scalable, and maintainable multi-agent system!
