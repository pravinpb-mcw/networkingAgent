# Phoenix Standalone Server - Quick Start

## Problem: Phoenix UI Stops When Agent Stops

When you run the agent with integrated Phoenix, the UI stops when the agent exits. This means you lose access to traces.

## Solution: Standalone Phoenix Server

Run Phoenix as a **separate persistent server** that stays up 24/7, independent of your agents.

## How to Use

### Step 1: Start Phoenix Server (Terminal 1)

```bash
# Option A: Using Python
python start_phoenix_standalone.py

# Option B: Using batch file  
start_phoenix_standalone.bat

# Option C: Custom port
python start_phoenix_standalone.py --port 6007
```

You'll see:
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    PHOENIX OBSERVABILITY SERVER (STANDALONE)                 ║
╚══════════════════════════════════════════════════════════════════════════════╝

✅ PHOENIX SERVER IS RUNNING

   📊 Dashboard: http://localhost:6006
   📁 Data stored in: E:\network of obserbility\networkingAgent\.phoenix
   
   🔄 Agents can now connect and send traces to this server
   🌐 UI will remain available even after agents stop
```

### Step 2: Run Your Agent (Terminal 2)

```bash
python agents\risk_score_agent.py
```

The agent will send traces to the Phoenix server on port 6006.

### Step 3: View Traces Anytime

Open browser: **http://localhost:6006**

- ✅ View traces while agent is running
- ✅ View traces after agent stops
- ✅ Traces persist across multiple agent runs
- ✅ No temp directory errors

### Step 4: Stop When Done

**Stop Agent:** Just exit the agent (Ctrl+C or let it finish)
- Phoenix server **keeps running**
- UI remains accessible
- All data preserved

**Stop Phoenix:** Press Ctrl+C in the Phoenix server terminal
- Safely shuts down
- Data saved in `.phoenix/` directory

## Benefits

| Integrated Phoenix | Standalone Phoenix Server |
|-------------------|--------------------------|
| ❌ Stops with agent | ✅ Runs independently |
| ❌ Temp directory errors | ✅ Persistent database |
| ❌ Traces lost on exit | ✅ Traces always available |
| ⚠️ Mixed with agent logs | ✅ Clean separation |

## Data Storage

All Phoenix data is stored in:
```
networkingAgent/.phoenix/
├── phoenix.db          # Main database (persistent!)
├── exports/            # Exported data
├── inferences/         # LLM inference data
└── trace_datasets/     # Trace datasets
```

This data **persists** and is available every time you start the Phoenix server.

## Quick Commands

```bash
# Start Phoenix server
python start_phoenix_standalone.py

# Run agent (in another terminal)
python agents\risk_score_agent.py --continuous 10

# Open UI in browser
http://localhost:6006

# Stop agent: Ctrl+C
# Phoenix keeps running ✅

# View past traces anytime
http://localhost:6006

# Stop Phoenix when done: Ctrl+C
```

## Troubleshooting

**Q: Can I run multiple agents with one Phoenix server?**  
A: Yes! All agents on port 6006 will send traces to the same Phoenix server.

**Q: What if port 6006 is in use?**  
A: Use custom port: `python start_phoenix_standalone.py --port 6007`

**Q: Do I still see temp directory errors?**  
A: No! Standalone Phoenix uses persistent storage only.

**Q: Can I close my browser and come back later?**  
A: Yes! Just reopen http://localhost:6006 anytime while Phoenix is running.

## Recommended Setup

**For Development:**
1. Start standalone Phoenix server once in the morning
2. Run agents throughout the day
3. View traces anytime in browser
4. Stop Phoenix at end of day

**For Production:**
- Run Phoenix as a Windows service
- Use Task Scheduler to auto-start on boot
- Access UI remotely via network

---

**That's it!** Now you have a persistent Phoenix dashboard that stays online regardless of your agents. 🎉
