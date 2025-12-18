# 📊 How to View Evaluations in Phoenix Dashboard

## ✅ Evaluations are Now Logged to Phoenix UI!

The evaluations are logged directly to Phoenix and appear as **annotations on traces**, not in a separate "Evaluations" tab.

## 🌐 View Evaluations in Dashboard

### Step 1: Open Phoenix Dashboard
Go to: **http://localhost:6006**

### Step 2: Go to Traces View
- Phoenix shows evaluations as **annotations** on individual spans
- Click on **"Traces"** in the left sidebar
- Or go directly to: **http://localhost:6006**

### Step 3: Filter by Hallucination Annotation
- Look for the **"Annotations"** or **"Evaluations"** filter panel
- Select **"Hallucination"** annotation
- You'll see all spans that have been evaluated

### Step 4: View Individual Evaluation Details
- Click on any trace/span that has the "Hallucination" annotation
- In the span details panel, look for:
  - **Evaluation Name**: "Hallucination"
  - **Score**: 1.0 (factual) or 0.0 (hallucinated)
  - **Label**: "factual" or "hallucinated"
  - **Explanation**: Detailed reasoning from Mixtral

## 📈 What You'll See

### In Traces View:
- Spans with evaluation annotations will have a badge/indicator
- Filter panel shows "Hallucination" as an available annotation
- Click spans to see full evaluation details in side panel

### Evaluation Details (in span panel):
- **Score**: Numeric score (0.0 = hallucinated, 1.0 = factual)
- **Label**: Categorical result (factual/hallucinated)
- **Explanation**: Why Mixtral gave this score
- **Timestamp**: When evaluation ran

## 🔍 Alternative: Use Phoenix Projects View

Some Phoenix versions show evaluations in Projects:
1. Click **"Projects"** in sidebar
2. Select your project (usually "default")
3. Look for evaluation metrics/summary

## 💡 Key Points

**Evaluations in Phoenix appear as:**
- ✅ **Annotations on spans** in Traces view (main way to see them)
- ✅ **Filterable** - you can filter traces by "Hallucination" annotation  
- ✅ **Detailed view** - click span to see full evaluation explanation

**NOT a separate "Evaluations" tab** - Phoenix integrates evaluations directly into the trace view.

## 📊 Data Storage

All evaluations are saved in:
- **Database**: `.phoenix/phoenix_traces.db` (as span annotations)
- **CSV Backup**: `phoenix_eval_results.csv` (for export/analysis)
- **Dashboard UI**: Visible as annotations in http://localhost:6006

## 🔄 Auto-Evaluation

Evaluations run automatically every 60 seconds:
- Fetches latest LLM spans from agents
- Runs Mixtral evaluation on each
- Logs results to dashboard
- Updates visualization in real-time

## 💡 Tips

### To see evaluations populate:
1. ✅ Phoenix server running: `python phoenix_persistent.py --auto-eval`
2. ✅ Run an agent: `python agents/risk_score_agent.py`
3. ✅ Wait 60 seconds for auto-eval (or check immediately in logs)
4. ✅ Refresh dashboard: http://localhost:6006/projects

### Troubleshooting "No Evaluations" in Dashboard:
- **Check terminal output**: You should see "📊 ✅ Evaluation results logged to Phoenix dashboard!"
- **Verify spans exist**: Go to "Traces" tab first, make sure agent calls are being tracked
- **Check Projects tab**: Evaluations are under Projects → Your Project → Evaluations
- **Restart Phoenix**: Sometimes UI needs refresh after first eval

## 📊 Data Persistence

All evaluations are saved in:
- **Database**: `.phoenix/phoenix_traces.db` (persistent)
- **CSV Backup**: `phoenix_eval_results.csv` (for export/analysis)
- **Dashboard UI**: Live view at http://localhost:6006/projects

## 🎯 Example Workflow

```bash
# Terminal 1: Start Phoenix with auto-eval
cd networkingAgent
python phoenix_persistent.py --auto-eval

# Terminal 2: Run your agent
python agents/risk_score_agent.py

# Browser: View evaluations
Open: http://localhost:6006/projects
Click: Evaluations tab
```

## 🔍 What Gets Evaluated

Every LLM call from your agents:
- **Input**: User query + context
- **Output**: Agent's response
- **Reference**: Original input (for hallucination detection)
- **Evaluator**: Mixtral 8x7B running on Ollama

The evaluator checks if the output is grounded in the reference/input or if it contains hallucinated information.

---

**🎉 Your evaluations are now fully integrated with Phoenix dashboard!**
No more CSV-only results - everything is visualized in the UI.
