# Explainability Setup - Quick Reference

## What's New

Your agents now have **FULL EXPLAINABILITY** for every action they take!

Every tool call, metric calculation, and decision is:
- ✅ **Explained** with reasoning
- ✅ **Checked** for hallucinations  
- ✅ **Logged** to Phoenix dashboard
- ✅ **Saved** to persistent files

## Quick Start (3 Steps)

### 1. Run the Demo

See explainability in action:

```bash
python demo_explainability.py
```

This demonstrates:
- Tool call explanations
- Metric calculations
- Decision justification
- Hallucination detection

### 2. Start the Explainable Agent

```bash
run_explainable_agent.bat
```

Or manually:

```bash
python agents/risk_score_agent_with_explainability.py --continuous 15
```

### 3. View in Phoenix Dashboard

Open browser: **http://localhost:6006**

You'll see:
- All agent traces
- Evaluation results
- Hallucination detection
- Explanation metadata

## Files Created

### Core Module
- **`core/explainability.py`** - Main explainability tracker with hallucination detection

### Agent with Explainability
- **`agents/risk_score_agent_with_explainability.py`** - Risk score agent with full explanations

### Documentation
- **`EXPLAINABILITY_GUIDE.md`** - Complete guide (read this for details!)

### Scripts
- **`demo_explainability.py`** - Interactive demonstration
- **`run_explainable_agent.bat`** - Quick launcher

### Output
- **`explanations/`** - Folder where explanation logs are saved (created automatically)

## Key Features

### 1. Explain Every Tool Call

```python
explainer.explain_tool_call(
    tool_name="get_wireless_latency_history",
    tool_input={"network_id": "L_123", "device_serial": "Q2AB..."},
    tool_output=latency_data,
    decision_reasoning="Need latency metrics to calculate risk score"
)
```

### 2. Explain Metric Calculations

```python
explainer.explain_metric_calculation(
    metric_name="risk_score",
    inputs={"latency": 45, "jitter": 12, "snr": 22},
    formula="0.25*lat + 0.20*jit + 0.15*snr",
    result=52.5,
    interpretation="Temporary Degradation - elevated latency"
)
```

### 3. Explain Decisions

```python
explainer.explain_decision(
    decision_point="Risk classification",
    chosen_option="Temporary Degradation",
    alternatives=["Stable", "Sustained Degradation", "Likely Failure"],
    reasoning="Risk score 52.5 falls in 21-40 range",
    supporting_data={"score": 52.5, "range": "21-40"}
)
```

### 4. Check for Hallucinations

```python
check = explainer.check_hallucination(
    output="AP-001 has risk score 52.5",
    context="Measured risk score: 52.5",
    query="What is the risk score?"
)

if check.is_hallucinated:
    print(f"⚠️ HALLUCINATION: {check.explanation}")
else:
    print(f"✅ FACTUAL (confidence: {check.confidence:.0%})")
```

## Phoenix Dashboard

### What You See

**Traces Panel:**
- Every LLM call
- Every tool invocation
- Input/output for each step
- Duration and token usage

**Evaluation Panel:**
- Hallucination detection results
- Factual vs hallucinated breakdown
- Confidence scores
- Judge model explanations

**Metrics Panel:**
- Average confidence over time
- Hallucination rate
- Actions by type
- Performance metrics

## Configuration

### Set API Keys

For hallucination detection, you need a judge model.

**Option 1: OpenAI**

```bash
# In .env file
OPENAI_API_KEY=sk-...
```

**Option 2: Anthropic Claude**

```bash
# In .env file
ANTHROPIC_API_KEY=...
ANTHROPIC_BASE_URL=https://api.anthropic.com
```

### Customize Phoenix Port

```bash
python agents/risk_score_agent_with_explainability.py --phoenix-port 6007
```

### Disable Explainability

```bash
python agents/risk_score_agent_with_explainability.py --no-explainability
```

## Example Output

When running the explainable agent, you'll see:

```
╔══════════════════════════════════════════════════════════════════════════════╗
║           RISK SCORE AGENT WITH FULL EXPLAINABILITY                         ║
╚══════════════════════════════════════════════════════════════════════════════╝

🔍 Initializing Phoenix observability...
✅ Phoenix UI: http://localhost:6006

Initializing agent (explainability: ON)...
✅ Agent ready with FULL EXPLAINABILITY

================================================================================
EXPLAINABILITY ENABLED
================================================================================
Every action will be:
  ✅ Explained with reasoning
  ✅ Checked for hallucinations
  ✅ Logged to Phoenix dashboard
  ✅ Saved to ./explanations/ folder

View real-time explanations at: http://localhost:6006
================================================================================

[10:30:45] Calculation #1
✅ Complete
   ✅ Output verified (confidence: 92%)

[Shutdown]
================================================================================
EXPLAINABILITY SUMMARY - RiskScoreAgent
================================================================================
Total Actions Explained: 47
Average Confidence: 91.3%

Actions by Type:
  - tool_call: 15
  - metric_calculation: 10
  - decision: 8
  - llm_call: 12
  - initialization: 2

Session Log: explanations/RiskScoreAgent_20251218_103045.jsonl
================================================================================
```

## Troubleshooting

### "No API key found for judge model"

Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in your `.env` file.

### "Could not connect to Phoenix"

Start Phoenix first:

```bash
python phoenix_persistent.py --auto-eval
```

### "Hallucination evaluator not available"

Install Phoenix evals:

```bash
pip install arize-phoenix[evals]
```

## Next Steps

1. ✅ **Read the full guide:** [EXPLAINABILITY_GUIDE.md](EXPLAINABILITY_GUIDE.md)

2. ✅ **Run the demo:** `python demo_explainability.py`

3. ✅ **Start the agent:** `run_explainable_agent.bat`

4. ✅ **Open Phoenix:** http://localhost:6006

5. ✅ **Customize** for your other agents (nearest AP, monitoring, etc.)

## Integration with Other Agents

To add explainability to your other agents:

```python
# Import the tracker
from core.explainability import create_explainability_tracker

# In your agent's __init__:
self.explainer = create_explainability_tracker(
    agent_name="YourAgentName",
    phoenix_endpoint="http://localhost:6006",
    enable=True
)

# In your workflow:
self.explainer.explain_tool_call(...)
self.explainer.explain_metric_calculation(...)
self.explainer.explain_decision(...)
self.explainer.check_hallucination(...)
```

See [risk_score_agent_with_explainability.py](agents/risk_score_agent_with_explainability.py) for a complete example.

---

**Questions?** Read the full guide: [EXPLAINABILITY_GUIDE.md](EXPLAINABILITY_GUIDE.md)
