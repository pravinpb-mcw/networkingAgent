# Explainability Guide - Arize Phoenix Integration

## Overview

This guide explains how to use **full explainability** with your network observability agents. Every action taken by the agents is now explained, justified, and checked for hallucinations.

## What You Get

### 1. **Explainability for Every Action**

Every action taken by your agents is now explained:

- **Tool Calls**: WHY each tool was chosen
- **Metric Calculations**: HOW scores were computed  
- **Decisions**: WHY a classification was assigned
- **Hallucination Checks**: WHAT is factual vs fabricated
- **Error Analysis**: WHY failures occurred

### 2. **Phoenix Dashboard Visualization**

All explanations are logged to Phoenix and visible in the dashboard:

- **Traces Panel**: See every LLM call, tool invocation, and span
- **Evaluation Panel**: View hallucination detection results
- **Metrics Panel**: Track explanation confidence scores
- **Per-Example Results**: Drill into individual decisions

### 3. **Automatic Hallucination Detection**

Every LLM output is checked for hallucinations using a judge model (GPT-4 or Claude):

```
Query: "What are the risk scores?"
Context: "Network metrics from Meraki API"
Response: "AP-001 has risk score 45.2 due to high latency..."

✅ FACTUAL - All claims supported by context
Confidence: 92%
```

### 4. **Persistent Explanation Logs**

All explanations are saved to JSONL files in `./explanations/`:

```json
{
  "action_id": "RiskScoreAgent_1734567890.123",
  "action_type": "metric_calculation",
  "timestamp": "2025-12-18T10:30:45",
  "input_context": "Latency: 45ms, Jitter: 12ms",
  "output_result": "Risk Score: 52.5",
  "explanation": "Risk score calculated using weighted formula",
  "reasoning": "Latency (45ms) → score 50, Jitter (12ms) → score 50...",
  "confidence": 0.95
}
```

---

## Quick Start

### Option 1: Run Explainable Agent (Recommended)

```batch
run_explainable_agent.bat
```

This starts:
- Phoenix UI on http://localhost:6006
- Risk Score Agent with explanations
- Continuous calculation every 15 seconds
- Hallucination detection on all outputs

### Option 2: Manual Python Execution

```bash
# Single calculation with explanations
python agents/risk_score_agent_with_explainability.py

# Continuous mode (every 10 seconds)
python agents/risk_score_agent_with_explainability.py --continuous 10

# Continuous mode with custom Phoenix port
python agents/risk_score_agent_with_explainability.py --continuous 15 --phoenix-port 6006
```

### Option 3: Disable Explainability

```bash
# Run without explanations (faster, no judge model calls)
python agents/risk_score_agent_with_explainability.py --no-explainability
```

---

## How It Works

### 1. Initialization

When the agent starts, the explainability tracker is created:

```python
from core.explainability import create_explainability_tracker

explainer = create_explainability_tracker(
    agent_name="RiskScoreAgent",
    phoenix_endpoint="http://localhost:6006",
    judge_model="gpt-4o",  # or "claude-sonnet-4"
    enable=True
)
```

### 2. Explaining Tool Calls

Every time a tool is called, the reason is logged:

```python
# Agent calls a tool
tool_output = call_tool("get_wireless_latency_history", {
    "network_id": "L_123",
    "device_serial": "Q2AB-CD3E-FGH4"
})

# Explainer logs WHY this tool was called
explainer.explain_tool_call(
    tool_name="get_wireless_latency_history",
    tool_input={"network_id": "L_123", "device_serial": "Q2AB-CD3E-FGH4"},
    tool_output=tool_output,
    decision_reasoning="Need latency metrics to calculate risk score"
)
```

**What you see in Phoenix:**
- Tool name and parameters
- Output data
- Reasoning for calling this tool
- Timestamp and duration

### 3. Explaining Metric Calculations

Every metric calculation is transparent:

```python
explainer.explain_metric_calculation(
    metric_name="risk_score",
    inputs={
        "latency": 45,
        "jitter": 12,
        "retransmissions": 25,
        "snr": 22,
        "clients": 15,
        "auth_failures": 2
    },
    formula="0.25*latency + 0.20*jitter + 0.20*retrans + 0.15*snr + 0.10*load + 0.10*auth",
    result=52.5,
    interpretation="Temporary Degradation - elevated latency and jitter"
)
```

**What you see in Phoenix:**
- Raw input values
- Formula used
- Step-by-step calculation
- Final result
- Human-readable interpretation

### 4. Explaining Decisions

Every decision point is justified:

```python
explainer.explain_decision(
    decision_point="Risk classification for AP-001",
    chosen_option="Temporary Degradation",
    alternatives=["Stable", "Sustained Degradation", "Likely Failure"],
    reasoning="Risk score 52.5 falls in 21-40 range, indicating temporary issues",
    supporting_data={
        "risk_score": 52.5,
        "threshold_range": "21-40",
        "primary_issues": ["latency", "jitter"]
    }
)
```

**What you see in Phoenix:**
- Decision being made
- Options considered
- Chosen option
- Reasoning with supporting data
- Confidence score

### 5. Hallucination Detection

Every LLM output is checked for hallucinations:

```python
hallucination_check = explainer.check_hallucination(
    output="AP-001 has risk score 52.5 due to high latency of 45ms",
    context="Latency: 45ms, Risk Score: 52.5 calculated from metrics",
    query="What is the risk score for AP-001?"
)

if hallucination_check.is_hallucinated:
    print(f"⚠️ HALLUCINATION: {hallucination_check.explanation}")
    print(f"Unsupported claims: {hallucination_check.unsupported_claims}")
else:
    print(f"✅ FACTUAL (confidence: {hallucination_check.confidence:.0%})")
```

**What you see in Phoenix:**
- Hallucination label (factual/hallucinated)
- Confidence score
- Explanation from judge model
- Supporting facts from context
- Unsupported claims (if hallucinated)

---

## Phoenix Dashboard Guide

### Accessing the Dashboard

1. Start the explainable agent:
   ```bash
   run_explainable_agent.bat
   ```

2. Open browser to: **http://localhost:6006**

3. You'll see the Phoenix dashboard with multiple panels

### Dashboard Panels

#### 1. **Traces Panel**

Shows every action as a hierarchical trace:

```
📊 Trace: risk-agent-20251218-103045
  ├─ 🔵 LLM Call (Claude Sonnet 4)
  │   ├─ Input: "Calculate risk scores for all APs..."
  │   ├─ Output: "Discovered 5 APs, calculating..."
  │   └─ Duration: 2.3s
  │
  ├─ 🟢 Tool: get_network_topology_link_layer
  │   ├─ Input: {network_id: "L_123"}
  │   ├─ Output: {...topology data...}
  │   └─ Duration: 0.5s
  │
  ├─ 🟢 Tool: get_wireless_latency_history
  │   ├─ Input: {device_serial: "Q2AB-CD3E-FGH4"}
  │   ├─ Output: {...latency data...}
  │   └─ Duration: 0.3s
  │
  └─ 🔵 LLM Call (Explanation)
      ├─ Input: "Explain the risk score calculation..."
      ├─ Output: "Risk score 52.5 because..."
      └─ Duration: 1.2s
```

**Click on any span** to see:
- Full input/output
- Metadata
- Explanation
- Token usage
- Error details (if any)

#### 2. **Evaluation Panel**

Shows hallucination detection results:

```
📊 Evaluations

Total Evaluated: 45
Factual: 42 (93%)
Hallucinated: 3 (7%)

Recent Evaluations:
✅ Factual | Confidence: 95% | "AP-001 risk score is 52.5"
✅ Factual | Confidence: 88% | "5 APs discovered in network"
⚠️ Hallucinated | Confidence: 78% | "AP-001 will fail within 2 hours"
```

**Click on an evaluation** to see:
- Full output text
- Reference context
- Judge model's reasoning
- Supporting facts
- Unsupported claims

#### 3. **Metrics Panel**

Track explanation confidence over time:

```
📈 Explanation Metrics

Average Confidence: 91%
Hallucination Rate: 7%

Confidence by Action Type:
- Tool Calls: 95%
- Metric Calculations: 98%
- Decisions: 85%
- LLM Calls: 88%
```

#### 4. **Per-Example Results**

Drill into individual decisions:

```
🔍 Example: Risk Score Calculation for AP-001

Input Context:
- Latency: 45ms
- Jitter: 12ms
- Retransmissions: 25/min
- SNR: 22 dB
- Clients: 15
- Auth Failures: 2/hr

Calculation:
latency_score = 50 (45ms is in 30-60ms range)
jitter_score = 50 (12ms is in 10-20ms range)
retrans_score = 50 (25/min is in 20-35/min range)
snr_score = 50 (22 dB is in 20-25 dB range)
load_score = 20 (15 clients is <20 range)
auth_score = 20 (2/hr is <3/hr range)

Final Score:
0.25*50 + 0.20*50 + 0.20*50 + 0.15*50 + 0.10*20 + 0.10*20 = 52.5

Classification: Temporary Degradation (21-40 range)

Hallucination Check: ✅ FACTUAL
Confidence: 92%
Explanation: All values are supported by metric data
```

---

## Explanation Storage

### File Structure

Explanations are saved to JSONL files:

```
networkingAgent/
  explanations/
    RiskScoreAgent_20251218_103045.jsonl
    RiskScoreAgent_20251218_110230.jsonl
    ...
```

Each file contains one explanation per line:

```jsonl
{"action_id": "RiskScoreAgent_1734567890.123", "action_type": "initialization", ...}
{"action_id": "RiskScoreAgent_1734567891.456", "action_type": "tool_call", ...}
{"action_id": "RiskScoreAgent_1734567892.789", "action_type": "metric_calculation", ...}
```

### Reading Explanation Logs

```python
import json

# Read all explanations from a session
with open("explanations/RiskScoreAgent_20251218_103045.jsonl", "r") as f:
    explanations = [json.loads(line) for line in f]

# Filter by action type
tool_calls = [e for e in explanations if e["action_type"] == "tool_call"]
metrics = [e for e in explanations if e["action_type"] == "metric_calculation"]

# Find low-confidence explanations
low_confidence = [e for e in explanations if e["confidence"] < 0.7]

print(f"Low confidence actions: {len(low_confidence)}")
for exp in low_confidence:
    print(f"  - {exp['action_type']}: {exp['explanation']}")
```

### Session Summary

At the end of each session, a summary is printed:

```
================================================================================
EXPLAINABILITY SUMMARY - RiskScoreAgent
================================================================================
Total Actions Explained: 127
Average Confidence: 91.3%

Actions by Type:
  - tool_call: 45
  - metric_calculation: 30
  - decision: 25
  - llm_call: 20
  - initialization: 5
  - error: 2

Session Log: explanations/RiskScoreAgent_20251218_103045.jsonl
================================================================================
```

---

## Configuration

### Judge Model Selection

The explainability system uses a "judge" LLM to generate explanations and detect hallucinations.

**Option 1: OpenAI GPT-4**

```bash
# Set in .env file
OPENAI_API_KEY=sk-...
```

```python
explainer = create_explainability_tracker(
    agent_name="RiskScoreAgent",
    judge_model="gpt-4o",  # Default
)
```

**Option 2: Anthropic Claude**

```bash
# Set in .env file
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

```python
explainer = create_explainability_tracker(
    agent_name="RiskScoreAgent",
    judge_model="claude-sonnet-4",
)
```

### Phoenix Endpoint

```python
explainer = create_explainability_tracker(
    agent_name="RiskScoreAgent",
    phoenix_endpoint="http://localhost:6006",  # Default
)
```

For remote Phoenix servers:

```python
explainer = create_explainability_tracker(
    agent_name="RiskScoreAgent",
    phoenix_endpoint="http://your-phoenix-server:6006",
)
```

### Enable/Disable Explainability

```bash
# Enable (default)
python agents/risk_score_agent_with_explainability.py

# Disable
python agents/risk_score_agent_with_explainability.py --no-explainability
```

In code:

```python
agent = ExplainableRiskScoreAgent(
    enable_explainability=True  # or False
)
```

---

## Advanced Usage

### Custom Explanations

Add your own explanations in code:

```python
# Explain a custom action
explainer.explain_action(
    action_type="custom_analysis",
    input_context="Analyzing trends for AP-001 over 24 hours",
    output_result="Detected degradation pattern starting at 10:00 AM",
    reference_context="Hourly metrics from Meraki API",
    metadata={
        "ap_serial": "Q2AB-CD3E-FGH4",
        "time_range": "24h",
        "pattern": "degradation"
    }
)
```

### Check Specific Outputs for Hallucinations

```python
# Check if a specific output is hallucinated
result = "AP-001 will fail in the next 2 hours due to critical metrics"
context = "Current risk score: 52.5 (Temporary Degradation)"

check = explainer.check_hallucination(
    output=result,
    context=context,
    query="Predict AP failure"
)

if check.is_hallucinated:
    print(f"⚠️ WARNING: {check.explanation}")
    print(f"Unsupported: {check.unsupported_claims}")
```

### Get Session Summary Programmatically

```python
summary = explainer.get_session_summary()

print(f"Total actions: {summary['total_actions']}")
print(f"Average confidence: {summary['average_confidence']:.2%}")

for action_type, count in summary['actions_by_type'].items():
    print(f"  {action_type}: {count}")
```

---

## Troubleshooting

### Issue: No Explanations in Phoenix Dashboard

**Solution:**
1. Check if Phoenix is running: http://localhost:6006
2. Verify Phoenix endpoint in code
3. Ensure evaluations are logged:
   ```python
   if explainer.phoenix_client:
       print("✅ Connected to Phoenix")
   else:
       print("❌ Not connected to Phoenix")
   ```

### Issue: Hallucination Checks Not Working

**Solution:**
1. Check API key is set:
   ```bash
   echo $OPENAI_API_KEY
   # or
   echo $ANTHROPIC_API_KEY
   ```

2. Verify evaluator is initialized:
   ```python
   if explainer.hallucination_evaluator:
       print("✅ Evaluator ready")
   else:
       print("❌ No evaluator")
   ```

3. Check logs for errors:
   ```
   ⚠️ No API key found for judge model
   ```

### Issue: Low Confidence Scores

**Cause:** Judge model is uncertain about the output quality.

**Solution:**
1. Provide more context to the agent
2. Use more specific prompts
3. Check if reference context matches output
4. Verify metrics are calculated correctly

### Issue: High Hallucination Rate

**Cause:** LLM is generating unsupported claims.

**Solution:**
1. Review agent prompts - be more specific
2. Provide better context/reference data
3. Use lower temperature (0-0.3) for LLM
4. Add constraints to prevent speculation

---

## Best Practices

### 1. Always Provide Context

❌ **Bad:**
```python
explainer.explain_action(
    action_type="calculation",
    input_context="Some data",
    output_result="42",
    reference_context=""
)
```

✅ **Good:**
```python
explainer.explain_action(
    action_type="risk_calculation",
    input_context="Latency: 45ms, Jitter: 12ms, SNR: 22dB from Meraki API",
    output_result="Risk Score: 52.5 (Temporary Degradation)",
    reference_context="Risk formula: 0.25*lat + 0.20*jit + 0.15*snr with thresholds <30=good, 30-60=warn, >60=critical",
    metadata={"ap_serial": "Q2AB-CD3E-FGH4"}
)
```

### 2. Explain Decisions, Not Just Actions

❌ **Bad:**
```python
# Just log that a decision was made
risk_class = "Temporary Degradation"
```

✅ **Good:**
```python
# Explain WHY this classification was chosen
explainer.explain_decision(
    decision_point="Risk classification",
    chosen_option="Temporary Degradation",
    alternatives=["Stable", "Sustained Degradation", "Likely Failure"],
    reasoning=f"Risk score {risk_score} falls in 21-40 range",
    supporting_data={"score": risk_score, "range": "21-40"}
)
```

### 3. Check Critical Outputs for Hallucinations

```python
# For critical decisions, always verify
critical_output = agent_response["mitigation_plan"]

check = explainer.check_hallucination(
    output=critical_output,
    context=current_network_state,
    query="Generate mitigation plan"
)

if check.is_hallucinated:
    logger.error("Cannot use hallucinated mitigation plan!")
    # Retry or use fallback
```

### 4. Review Explanation Logs Regularly

```bash
# Check recent explanations
tail -n 50 explanations/RiskScoreAgent_*.jsonl | jq '.explanation'

# Find low-confidence actions
cat explanations/RiskScoreAgent_*.jsonl | jq 'select(.confidence < 0.7)'

# Count hallucinations
cat explanations/RiskScoreAgent_*.jsonl | jq 'select(.action_type == "llm_call")' | grep "hallucinated"
```

---

## Example Workflow

Here's a complete example of an explainable workflow:

```python
from core.explainability import create_explainability_tracker

# 1. Initialize explainability
explainer = create_explainability_tracker(
    agent_name="RiskScoreAgent",
    phoenix_endpoint="http://localhost:6006"
)

# 2. Explain tool call
explainer.explain_tool_call(
    tool_name="get_wireless_latency_history",
    tool_input={"network_id": "L_123", "device_serial": "Q2AB-CD3E-FGH4"},
    tool_output=latency_data,
    decision_reasoning="Need latency metrics to calculate risk score for AP-001"
)

# 3. Explain metric calculation
explainer.explain_metric_calculation(
    metric_name="latency_score",
    inputs={"raw_latency": 45},
    formula="Map 45ms to 0-100 scale using thresholds",
    result=50,
    interpretation="50/100 - Latency in warning range (30-60ms)"
)

# 4. Explain final decision
explainer.explain_decision(
    decision_point="Risk classification for AP-001",
    chosen_option="Temporary Degradation",
    alternatives=["Stable", "Sustained Degradation", "Likely Failure"],
    reasoning="Composite risk score 52.5 falls in 21-40 range indicating temporary issues",
    supporting_data={
        "risk_score": 52.5,
        "components": {
            "latency": 50,
            "jitter": 50,
            "snr": 50,
            "load": 20,
            "auth": 20
        }
    }
)

# 5. Check for hallucinations
agent_output = "AP-001 shows temporary degradation with risk score 52.5"
check = explainer.check_hallucination(
    output=agent_output,
    context=f"Risk score: 52.5, Classification: Temporary Degradation",
    query="Summarize risk assessment"
)

if check.is_hallucinated:
    print(f"⚠️ HALLUCINATION: {check.explanation}")
else:
    print(f"✅ FACTUAL: {check.explanation}")

# 6. Get summary
summary = explainer.get_session_summary()
print(f"\nTotal actions: {summary['total_actions']}")
print(f"Avg confidence: {summary['average_confidence']:.2%}")
```

---

## Summary

You now have **full explainability** for every action your agents take:

✅ **Tool calls** - WHY each tool was chosen  
✅ **Metrics** - HOW calculations were done  
✅ **Decisions** - WHY classifications were assigned  
✅ **Hallucination checks** - WHAT is factual vs fabricated  
✅ **Phoenix dashboard** - Visual exploration of all traces  
✅ **Persistent logs** - Complete audit trail  

### Next Steps

1. **Run the explainable agent:**
   ```bash
   run_explainable_agent.bat
   ```

2. **Open Phoenix dashboard:**
   ```
   http://localhost:6006
   ```

3. **Watch explanations in real-time** as the agent works

4. **Review explanation logs** in `./explanations/` folder

5. **Customize explanations** for your specific use cases

---

## Additional Resources

- [Phoenix Documentation](https://docs.arize.com/phoenix)
- [Hallucination Evaluation Guide](https://docs.arize.com/phoenix/evaluation/hallucination-evaluation)
- [LLM Tracing Guide](https://docs.arize.com/phoenix/tracing/llm-traces)
- [Evaluation Metrics](https://docs.arize.com/phoenix/evaluation/evaluation-metrics)
