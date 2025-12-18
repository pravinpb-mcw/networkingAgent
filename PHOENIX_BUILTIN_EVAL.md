# Using Phoenix Built-in Evaluation (No Custom Wrapper)

## Overview

Phoenix has **built-in evaluation features** that can provide explainability without custom code. Here's how to use them directly.

## What Phoenix Provides Out-of-the-Box

### 1. Automatic Tracing (Already Working)

Your agents already use Phoenix tracing via `phoenix_tracing.py`:

```python
from phoenix_tracing import initialize_phoenix

# This captures all LLM calls automatically
initialize_phoenix(
    project_name="Risk Score Agent",
    launch_ui=True,
    ui_port=6006,
    enable_langchain_instrumentation=True  # Auto-traces LangChain
)
```

✅ **What you get for free:**
- All LLM calls traced
- All tool calls captured
- Input/output logged
- Token usage tracked
- Timing information

### 2. Built-in Evaluators

Phoenix includes pre-built evaluators:

```python
from phoenix.evals import (
    HallucinationEvaluator,
    RelevanceEvaluator,
    QAEvaluator,
    run_evals
)
```

### 3. Phoenix Client for Data Retrieval

```python
from phoenix.session.client import Client

client = Client(endpoint="http://localhost:6006")
spans_df = client.get_spans_dataframe()
```

## Simple Setup (Built-in Only)

### Step 1: Just Use Phoenix Tracing

Your agents already have this:

```python
# In risk_score_agent.py (already present)
from phoenix_tracing import initialize_phoenix

initialize_phoenix(
    project_name="Risk Score Agent",
    launch_ui=True,
    ui_port=6006,
    enable_langchain_instrumentation=True
)

# Now run your agent - all LLM calls are traced automatically!
```

### Step 2: Run Evaluations After Traces Exist

Instead of evaluating during execution, evaluate after:

```python
#!/usr/bin/env python3
"""
Simple Phoenix evaluation using ONLY built-in features
"""

from phoenix.session.client import Client
from phoenix.evals import HallucinationEvaluator, run_evals
from phoenix.evals.models import OpenAIModel
import pandas as pd
import os

# Connect to running Phoenix server
client = Client(endpoint="http://localhost:6006")

# Get all spans
spans_df = client.get_spans_dataframe()

# Filter for LLM spans
llm_spans = spans_df[spans_df['span_kind'] == 'LLM']

print(f"Found {len(llm_spans)} LLM spans to evaluate")

# Prepare data for evaluator
eval_df = llm_spans.copy()
eval_df['input'] = eval_df['attributes.llm.input_messages'].astype(str)
eval_df['output'] = eval_df['attributes.llm.output_messages'].astype(str)
eval_df['reference'] = eval_df['input']  # Use input as reference

# Create evaluator
judge = OpenAIModel(model="gpt-4o", api_key=os.getenv("OPENAI_API_KEY"))
evaluator = HallucinationEvaluator(model=judge)

# Run evaluation
results = run_evals(
    dataframe=eval_df,
    evaluators=[evaluator],
    provide_explanation=True  # This gives you WHY
)

# View results
print(f"\nEvaluation Results:")
print(f"Total: {len(results)}")
print(f"Factual: {len(results[results['label'] == 'factual'])}")
print(f"Hallucinated: {len(results[results['label'] == 'hallucinated'])}")

# Show explanations
for idx, row in results.iterrows():
    if row['label'] == 'hallucinated':
        print(f"\n⚠️ HALLUCINATION DETECTED:")
        print(f"   Output: {row['output'][:100]}...")
        print(f"   Explanation: {row['explanation']}")

# Save results
results.to_csv("phoenix_eval_results.csv")
print(f"\n✅ Results saved to phoenix_eval_results.csv")
```

### Step 3: View in Phoenix Dashboard

Just open: **http://localhost:6006**

You'll see:
- All traces (automatic)
- Evaluation results (from Step 2)
- Explanations in the UI

## Comparison: Built-in vs Custom Wrapper

| Feature | Phoenix Built-in | Custom ExplainabilityTracker |
|---------|-----------------|------------------------------|
| **LLM Call Tracing** | ✅ Automatic | ✅ Automatic (same) |
| **Tool Call Tracing** | ✅ Automatic | ✅ Automatic (same) |
| **Hallucination Detection** | ✅ Yes (manual) | ✅ Yes (automatic) |
| **Evaluation Timing** | ⏱️ After traces exist | ⏱️ Real-time during execution |
| **Tool Choice Explanation** | ❌ No | ✅ Yes |
| **Metric Calculation Explanation** | ❌ No | ✅ Yes |
| **Decision Justification** | ❌ No | ✅ Yes |
| **Persistent JSONL Logs** | ❌ No (CSV only) | ✅ Yes |
| **Convenience Methods** | ❌ No | ✅ Yes (`explain_tool_call`, etc.) |
| **Code Changes Required** | ✅ Minimal | ⚠️ More integration |

## When to Use Which Approach

### Use Phoenix Built-in ONLY if:
- ✅ You only need LLM call explanations
- ✅ Batch evaluation after execution is fine
- ✅ You don't need custom explanation logic
- ✅ Phoenix dashboard UI is enough

### Use Custom ExplainabilityTracker if:
- ✅ You want explanations for tool choices
- ✅ You want metric calculation transparency
- ✅ You want real-time hallucination detection
- ✅ You want decision justification
- ✅ You want persistent JSONL logs

## Hybrid Approach (Recommended)

**Best of both worlds:**

1. **Use Phoenix tracing** (already working) for automatic capture
2. **Add custom explanations** only where Phoenix doesn't cover:
   - Tool selection reasoning
   - Metric calculation steps
   - Decision justification

```python
# Minimal hybrid approach
from phoenix_tracing import initialize_phoenix
from phoenix.evals import HallucinationEvaluator, run_evals
from phoenix.session.client import Client

# 1. Phoenix handles LLM tracing automatically
initialize_phoenix(...)

# 2. Add manual explanations ONLY for non-LLM actions
def calculate_risk_score(metrics):
    # Calculate
    score = 0.25 * metrics['latency'] + 0.20 * metrics['jitter'] + ...
    
    # Add explanation (simple logging)
    print(f"EXPLANATION: Risk score {score} calculated from:")
    print(f"  - Latency: {metrics['latency']} * 0.25")
    print(f"  - Jitter: {metrics['jitter']} * 0.20")
    # ... etc
    
    return score

# 3. Run batch hallucination check after execution
client = Client()
spans = client.get_spans_dataframe()
results = run_evals(spans, evaluators=[HallucinationEvaluator()])
```

## Simplest Possible Setup

**Already working in your agents:**

1. **Start Phoenix:** `python phoenix_persistent.py --auto-eval`
2. **Run your agent:** `python agents/risk_score_agent.py --continuous`
3. **View traces:** http://localhost:6006

That's it! Phoenix automatically:
- ✅ Traces all LLM calls
- ✅ Captures tool invocations
- ✅ Shows input/output
- ✅ Runs evaluations (with `--auto-eval`)

## Conclusion

**You DON'T need the custom wrapper if:**
- Phoenix's automatic tracing is enough
- You're okay with batch evaluation
- LLM explanations are your main concern

**The custom wrapper adds value for:**
- Real-time explanations
- Tool/decision/metric transparency
- Convenience methods
- Custom explanation logic

**Both approaches work with Phoenix dashboard!**

Choose based on your needs. The simplest approach is just using what you already have in `phoenix_tracing.py`.
