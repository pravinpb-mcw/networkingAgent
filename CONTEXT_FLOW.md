# Context Flow: Observation Agent → Mitigation Agent

## Overview

The mitigation agent receives context from the observation agent through a **structured tool call interface**. The observation agent doesn't just pass raw data—it extracts, analyzes, and packages relevant information into a well-defined format.

---

## Context Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVATION AGENT (Network Monitor)                            │
│                                                                  │
│  Step 1: Gather Raw Data                                        │
│  ├─ Call get_device_loss_and_latency_history()                  │
│  │  └─ Returns: [{ts, latency, loss, jitter}, ...]              │
│  ├─ Call get_organization_uplinks_statuses()                    │
│  │  └─ Returns: [{serial, status, ip, ...}, ...]                │
│  └─ Call get_network_clients()                                  │
│     └─ Returns: [{id, status, ...}, ...]                        │
│                                                                  │
│  Step 2: Analyze & Detect Issues                                │
│  ├─ Extract MOST RECENT metrics from history                    │
│  ├─ Compare against thresholds:                                 │
│  │  • Latency: 75.5ms > 50ms threshold ❌ WARNING               │
│  │  • Packet Loss: 0.5% < 1% threshold ✅ OK                    │
│  │  • Jitter: 15.3ms > 10ms threshold ❌ WARNING                │
│  ├─ Filter uplinks for target device only                       │
│  └─ Determine severity: 'warning' or 'critical'                 │
│                                                                  │
│  Step 3: Package Context for Mitigation Agent                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Context Package (Tool Call Parameters)                  │   │
│  │  ─────────────────────────────────────────────────────   │   │
│  │  issue_type: "High Latency and Jitter"                   │   │
│  │  severity: "warning"                                      │   │
│  │  current_latency_ms: 75.5                                │   │
│  │  current_packet_loss_pct: 0.5                            │   │
│  │  current_jitter_ms: 15.3                                 │   │
│  │  uplink_status: "active"                                 │   │
│  │  additional_context: "Gradual increase over 30 mins.     │   │
│  │                      Uplink active. No client issues."   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                           │                                      │
│                           │ Tool Call via LLM                    │
│                           ▼                                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │
┌───────────────────────────┴─────────────────────────────────────┐
│  TOOL WRAPPER (_create_mitigation_tool)                         │
│                                                                  │
│  async def call_mitigation_agent(                               │
│      issue_type: str,              ← "High Latency and Jitter"  │
│      severity: str,                ← "warning"                  │
│      current_latency_ms: float,    ← 75.5                       │
│      current_packet_loss_pct: float,← 0.5                       │
│      current_jitter_ms: float,     ← 15.3                       │
│      uplink_status: str,           ← "active"                   │
│      additional_context: str       ← "Gradual increase..."      │
│  ):                                                              │
│      # Repackage into metrics dict                              │
│      metrics = {                                                 │
│          "latency_ms": current_latency_ms,                       │
│          "packet_loss_pct": current_packet_loss_pct,            │
│          "jitter_ms": current_jitter_ms,                         │
│          "uplink_status": uplink_status                          │
│      }                                                           │
│                                                                  │
│      # Call mitigation agent's generate method                  │
│      result = await mitigation_agent.generate_mitigation_strategy(│
│          issue_type=issue_type,                                  │
│          severity=severity,                                      │
│          metrics=metrics,                                        │
│          device_serial="Q2MN-Q3J9-YJHW",  ← From controller     │
│          network_id="L_...",               ← From controller     │
│          additional_context=additional_context                  │
│      )                                                           │
│                                                                  │
│      return result["strategy"]                                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │
┌─────────────────────────────┴───────────────────────────────────┐
│  MITIGATION STRATEGY AGENT                                       │
│                                                                  │
│  Receives Context Package:                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  INCIDENT DETAILS:                                        │  │
│  │  ─────────────────                                        │  │
│  │  Issue Type: High Latency and Jitter                      │  │
│  │  Severity: WARNING                                        │  │
│  │  Device Serial: Q2MN-Q3J9-YJHW                            │  │
│  │  Network ID: L_3947405073390239794                        │  │
│  │                                                            │  │
│  │  CURRENT METRICS:                                         │  │
│  │  ─────────────────                                        │  │
│  │  - latency_ms: 75.5                                       │  │
│  │  - packet_loss_pct: 0.5                                   │  │
│  │  - jitter_ms: 15.3                                        │  │
│  │  - uplink_status: active                                  │  │
│  │                                                            │  │
│  │  ADDITIONAL CONTEXT:                                      │  │
│  │  ─────────────────────                                    │  │
│  │  Gradual increase over 30 minutes. Uplink active.         │  │
│  │  No client issues detected.                               │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  Step 1: Gather MORE Context (calls its own tools)              │
│  ├─ get_device_loss_and_latency_history(Q2MN-Q3J9-YJHW)         │
│  │  Purpose: See historical trends, not just current snapshot   │
│  ├─ get_organization_uplinks_statuses(Q2MN-Q3J9-YJHW)           │
│  │  Purpose: Review uplink configuration details                │
│  ├─ get_network_settings(L_3947405073390239794)                 │
│  │  Purpose: Check current network configuration                │
│  └─ get_connectivity_monitoring(L_3947405073390239794)          │
│     Purpose: Review monitoring thresholds and settings          │
│                                                                  │
│  Step 2: Analyze Root Cause                                     │
│  ├─ Compare current metrics vs historical baseline              │
│  ├─ Identify patterns (gradual vs sudden)                       │
│  ├─ Check configuration for misconfigurations                   │
│  └─ Assess impact on services                                   │
│                                                                  │
│  Step 3: Generate Mitigation Strategy                           │
│  ├─ IMMEDIATE ACTIONS (0-5 min)                                 │
│  ├─ SHORT-TERM FIXES (5-30 min)                                 │
│  ├─ INVESTIGATION STEPS                                         │
│  ├─ LONG-TERM SOLUTIONS (1-24 hrs)                              │
│  └─ PREVENTIVE MEASURES                                         │
│                                                                  │
│  Returns: Comprehensive strategy document                       │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              │ Strategy returned to tool wrapper
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  OBSERVATION AGENT (receives strategy)                          │
│                                                                  │
│  Step 4: Integrate Strategy into Alert                          │
│  ├─ Receives full mitigation strategy as string                 │
│  ├─ Combines with issue details                                 │
│  └─ Calls send_network_alert() with complete message            │
│                                                                  │
│  Final Alert Message:                                            │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Network Issue Detected                                   │  │
│  │                                                            │  │
│  │  ISSUE: High Latency and Jitter                           │  │
│  │                                                            │  │
│  │  CURRENT METRICS:                                         │  │
│  │  - Latency: 75.5ms (Threshold: 50ms)                      │  │
│  │  - Jitter: 15.3ms (Threshold: 10ms)                       │  │
│  │                                                            │  │
│  │  MITIGATION STRATEGY:                                     │  │
│  │  ════════════════════                                     │  │
│  │  [Full strategy from mitigation agent]                    │  │
│  │                                                            │  │
│  │  1. IMMEDIATE ACTIONS:                                    │  │
│  │     - Check for bandwidth saturation...                   │  │
│  │     - Verify no DDoS attack...                            │  │
│  │                                                            │  │
│  │  2. SHORT-TERM FIXES:                                     │  │
│  │     - Adjust QoS settings...                              │  │
│  │     - Tune connectivity monitoring...                     │  │
│  │                                                            │  │
│  │  [etc...]                                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           │                                      │
│                           │ Send to Teams/Slack                  │
│                           ▼                                      │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │   WEBHOOK    │
                    │ Teams/Slack  │
                    └──────────────┘
```

---

## Detailed Context Flow Analysis

### Phase 1: Observation Agent Gathers Raw Data

**Location:** `network_monitor_agent.py` - `check_network_state()`

The observation agent's LLM executes these tool calls:

```python
# Agent's internal reasoning (via LLM):
# "I need to check network metrics for device Q2MN-Q3J9-YJHW"

# Tool call 1: Get performance history
result1 = get_device_loss_and_latency_history(
    serial="Q2MN-Q3J9-YJHW",
    ip="8.8.8.8"
)
# Returns: [
#   {"ts": "2025-11-13T16:53:47", "latencyMs": 15.5, "lossPercent": 0.1, ...},
#   {"ts": "2025-11-13T17:23:47", "latencyMs": 45.2, "lossPercent": 0.3, ...},
#   {"ts": "2025-11-13T17:53:47", "latencyMs": 75.5, "lossPercent": 0.5, ...}  ← LATEST
# ]

# Tool call 2: Get uplink status
result2 = get_organization_uplinks_statuses()
# Returns: [
#   {"serial": "Q2MN-Q3J9-YJHW", "status": "active", "ip": "192.168.1.69", ...},
#   {"serial": "OTHER-DEVICE-123", "status": "failed", ...},  ← IGNORED
#   ...
# ]
```

**Key Point:** The observation agent has access to **ALL** the raw data but must extract only relevant information.

### Phase 2: Observation Agent Analyzes & Packages Context

**Location:** `network_monitor_agent.py` - Agent's LLM reasoning

The agent's LLM analyzes the data and decides:

```python
# Agent's reasoning (happens in LLM):
# "Latest metrics show latency 75.5ms > 50ms threshold"
# "Jitter 15.3ms > 10ms threshold"  
# "This is a WARNING level issue"
# "I should call generate_mitigation_strategy tool"

# The LLM formats the tool call:
{
    "tool": "generate_mitigation_strategy",
    "arguments": {
        "issue_type": "High Latency and Jitter",
        "severity": "warning",
        "current_latency_ms": 75.5,        # Extracted from LATEST entry
        "current_packet_loss_pct": 0.5,    # Extracted from LATEST entry
        "current_jitter_ms": 15.3,         # Extracted from LATEST entry
        "uplink_status": "active",         # Filtered for target device
        "additional_context": "Gradual increase over 30 minutes. Previous reading was 45.2ms at 17:23. Uplink is active. No client connection issues detected."
    }
}
```

**Critical Context Engineering:**
- ✅ Extracts **most recent** values from history array
- ✅ Filters uplink data to **target device only**
- ✅ Calculates **trends** (gradual vs sudden)
- ✅ Adds **contextual observations** in additional_context
- ✅ Determines **severity** based on thresholds

### Phase 3: Tool Wrapper Receives & Forwards

**Location:** `network_monitor_agent.py` - `_create_mitigation_tool()`

```python
async def call_mitigation_agent(
    issue_type: str,                      # ← "High Latency and Jitter"
    severity: str,                        # ← "warning"
    current_latency_ms: float,            # ← 75.5
    current_packet_loss_pct: float,       # ← 0.5
    current_jitter_ms: float,             # ← 15.3
    uplink_status: str = "unknown",       # ← "active"
    additional_context: str = ""          # ← "Gradual increase..."
) -> str:
    # Repackage as metrics dict
    metrics = {
        "latency_ms": current_latency_ms,
        "packet_loss_pct": current_packet_loss_pct,
        "jitter_ms": current_jitter_ms,
        "uplink_status": uplink_status
    }
    
    # Call mitigation agent with ENRICHED context
    result = await mitigation_agent.generate_mitigation_strategy(
        issue_type=issue_type,           # From observation agent's analysis
        severity=severity,                # From observation agent's analysis
        metrics=metrics,                  # From observation agent's extraction
        device_serial=target_device,      # From controller config
        network_id=target_network,        # From controller config
        additional_context=additional_context  # From observation agent
    )
    
    return result["strategy"]
```

**Context Enrichment:**
- Tool wrapper adds **device_serial** and **network_id** (known to controller)
- Packages individual metrics into a structured **metrics dict**
- Preserves all context from observation agent

### Phase 4: Mitigation Agent Receives Structured Context

**Location:** `mitigation_strategy_agent.py` - `generate_mitigation_strategy()`

The mitigation agent receives a **well-structured context package**:

```python
{
    "issue_type": "High Latency and Jitter",
    "severity": "warning",
    "metrics": {
        "latency_ms": 75.5,
        "packet_loss_pct": 0.5,
        "jitter_ms": 15.3,
        "uplink_status": "active"
    },
    "device_serial": "Q2MN-Q3J9-YJHW",
    "network_id": "L_3947405073390239794",
    "additional_context": "Gradual increase over 30 minutes..."
}
```

This is formatted into a **comprehensive prompt** for the mitigation agent's LLM:

```python
prompt = f"""
INCIDENT DETAILS:

Issue Type: {issue_type}                    # High Latency and Jitter
Severity: {severity.upper()}                # WARNING
Device Serial: {device_serial}              # Q2MN-Q3J9-YJHW
Network ID: {network_id}                    # L_3947405073390239794

CURRENT METRICS:
- latency_ms: 75.5
- packet_loss_pct: 0.5
- jitter_ms: 15.3
- uplink_status: active

ADDITIONAL CONTEXT:
Gradual increase over 30 minutes. Previous reading was 45.2ms...

TASK:
Generate a comprehensive mitigation strategy...

EXECUTION STEPS:
1. First, gather current configuration data:
   - Call get_device_loss_and_latency_history for Q2MN-Q3J9-YJHW to see trends
   - Call get_organization_uplinks_statuses for device Q2MN-Q3J9-YJHW
   - Call get_network_settings for L_3947405073390239794
   ...
"""
```

### Phase 5: Mitigation Agent Gathers Additional Context

**Location:** `mitigation_strategy_agent.py` - Agent's own tool calls

The mitigation agent's LLM now makes **its own tool calls** to gather more context:

```python
# Mitigation agent's reasoning:
# "I have the incident summary, but I need detailed configuration data"

# Makes its own tool calls:
history = get_device_loss_and_latency_history("Q2MN-Q3J9-YJHW")
# Gets FULL history to analyze trends

uplinks = get_organization_uplinks_statuses()
# Gets FULL uplink config (not just status)

settings = get_network_settings("L_3947405073390239794")
# Gets network configuration details

monitoring = get_connectivity_monitoring("L_3947405073390239794")
# Gets current monitoring thresholds
```

**Key Insight:** The mitigation agent:
- ✅ Receives **analyzed context** from observation agent
- ✅ Then gathers **additional raw data** for deeper analysis
- ✅ Combines both to create comprehensive strategy

### Phase 6: Strategy Returns to Observation Agent

**Location:** Back to `network_monitor_agent.py`

```python
# Observation agent's LLM receives the strategy as tool result
tool_result = """
# NETWORK MITIGATION STRATEGY - HIGH LATENCY INCIDENT

**INCIDENT SUMMARY:**
- Device: Q2MN-Q3J9-YJHW
- Issue: High Latency and Jitter
- Severity: WARNING

## 1. IMMEDIATE ACTIONS (0-5 minutes)
### 1.1 Verify Current Status
- Re-check device performance...
[full strategy continues...]
"""

# Agent then includes this in alert
send_network_alert(
    title="Network Alert: High Latency and Jitter",
    message=f"""
    Issue Detected: High Latency and Jitter
    
    CURRENT METRICS:
    - Latency: 75.5ms (Threshold: 50ms)
    - Jitter: 15.3ms (Threshold: 10ms)
    
    MITIGATION STRATEGY:
    {tool_result}
    """,
    status="warning"
)
```

---

## Context Information Flow Summary

### What Observation Agent Provides:
1. **Issue Classification** - What type of problem was detected
2. **Severity Assessment** - How critical is it
3. **Current Metrics** - Exact values at time of detection
4. **Trend Analysis** - Is it gradual or sudden
5. **Environmental Context** - Uplink status, client status, etc.
6. **Temporal Context** - When did it start, how long has it been happening

### What Mitigation Agent Adds:
1. **Historical Analysis** - Full performance history trends
2. **Configuration Review** - Current network and device settings
3. **Root Cause Hypothesis** - Why is this happening
4. **Remediation Steps** - What to do about it
5. **Risk Assessment** - Impact of each action
6. **Preventive Recommendations** - How to avoid recurrence

### The Power of This Design:

**Observation Agent:**
- Focused on **real-time monitoring**
- Lightweight prompts for **fast detection**
- Provides **just enough context** to trigger mitigation

**Mitigation Agent:**
- Focused on **deep analysis**
- Can take time to **gather comprehensive data**
- Generates **detailed, actionable strategies**

This separation allows:
- ✅ Fast detection (observation agent isn't slowed by strategy generation)
- ✅ Comprehensive remediation (mitigation agent has time to be thorough)
- ✅ Clear responsibilities (each agent has a focused role)

---

## Example: Complete Context Flow

```
TIME: 17:53:00

[1] Observation Agent detects issue
    Raw Data: latency=75.5ms, loss=0.5%, jitter=15.3ms
    Analysis: 75.5 > 50 threshold, 15.3 > 10 threshold
    Context Package Created:
    ├─ issue_type: "High Latency and Jitter"
    ├─ severity: "warning"
    ├─ metrics: {latency: 75.5, loss: 0.5, jitter: 15.3}
    ├─ uplink: "active"
    └─ context: "Gradual increase over 30 minutes"

[2] Tool wrapper enhances context
    Adds: device_serial, network_id
    Forwards to mitigation agent

[3] Mitigation agent receives context
    Receives: Complete incident package
    Parses: Issue type, severity, metrics, context
    Prompts LLM with structured incident details

[4] Mitigation agent gathers more data
    Calls: get_device_loss_and_latency_history()
    Calls: get_network_settings()
    Calls: get_connectivity_monitoring()
    Analyzes: Configuration + history + current state

[5] Mitigation agent generates strategy
    Creates: 5-phase mitigation plan
    Includes: Specific actions, timelines, risks
    Returns: Full strategy document (string)

[6] Observation agent receives strategy
    Integrates: Strategy into alert message
    Sends: Complete alert to webhook
    
TIME: 17:53:08 (8 seconds elapsed)
```

---

## Code References

| Component | File | Function/Method |
|-----------|------|-----------------|
| Context gathering | `network_monitor_agent.py` | `check_network_state()` |
| Context packaging | `network_monitor_agent.py` | Agent's LLM (via prompt) |
| Tool wrapper | `network_monitor_agent.py` | `_create_mitigation_tool()` |
| Context reception | `mitigation_strategy_agent.py` | `generate_mitigation_strategy()` |
| Strategy generation | `mitigation_strategy_agent.py` | Agent's LLM (via prompt) |
| Strategy integration | `network_monitor_agent.py` | Agent's LLM (tool result handling) |

---

**Last Updated:** November 13, 2025
