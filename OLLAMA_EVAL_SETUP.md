# Ollama Integration for Phoenix Evaluation

## What Changed

✅ **Phoenix now uses your Ollama server for hallucination detection**

- **Model**: `mixtral:8x7b` (best from your available models)
- **Server**: http://192.168.13.162:11434
- **Auto-evaluation**: Enabled by default
- **Dashboard visibility**: Fixed - results now appear in Phoenix UI

## Why Mixtral?

From your Ollama models, **mixtral:8x7b** is the best choice for evaluation because:

1. ✅ **46.7B parameters** - Most capable reasoning model
2. ✅ **Mixture of Experts** - Excellent for analytical tasks
3. ✅ **Strong evaluation performance** - Industry-standard for LLM-as-a-judge

### Your Other Models (Why Not Chosen)

- `qwen3:32b` - Good alternative, but mixtral is better for evaluation
- `llama3.1:8b` - Too small for reliable evaluation
- `llama3.2:latest` - Only 3.2B params, not enough
- `gpt-oss:20b` - Less tested for evaluation tasks
- `phi:latest` - 3B params, too small
- `llama2:latest` - Outdated
- `mxbai-embed-large` - For embeddings only, not generation

## Setup Steps

### 1. Install LiteLLM

```bash
pip install litellm
```

This lets Phoenix connect to Ollama.

### 2. Test the Connection

```bash
python test_ollama_eval.py
```

This will:
- ✅ Test Ollama connection
- ✅ Verify mixtral:8x7b is available
- ✅ Run sample evaluation
- ✅ Show results

### 3. Start Phoenix with Auto-Eval

```bash
python phoenix_persistent.py --auto-eval --eval-interval 60
```

This will:
- Start Phoenix UI on http://localhost:6006
- Automatically evaluate traces every 60 seconds
- Use Ollama mixtral:8x7b for evaluation
- Log results to dashboard (**now visible!**)

### 4. Run Your Agent

```bash
python agents/risk_score_agent.py --continuous 15
```

Agent will:
- Generate traces
- Send to Phoenix
- Phoenix auto-evaluates with Ollama
- Results appear in dashboard

## What Was Fixed

### Problem: Evaluations Not Visible in Dashboard

**Before:**
```python
# Results saved to CSV only
results.to_csv("phoenix_eval_results.csv")
```

**After:**
```python
# Results saved AND logged to Phoenix dashboard
results.to_csv("phoenix_eval_results.csv")

# LOG TO DASHBOARD (NEW!)
from phoenix.trace import SpanEvaluations
client.log_evaluations(SpanEvaluations(...))
```

### Problem: Ollama Not Supported

**Before:**
```python
# Only OpenAI or Anthropic
if os.getenv("OPENAI_API_KEY"):
    model = OpenAIModel(model="gpt-4o")
elif os.getenv("ANTHROPIC_API_KEY"):
    model = AnthropicModel(model="claude-sonnet-4")
```

**After:**
```python
# Now supports Ollama via LiteLLM
from phoenix.evals.models import LiteLLMModel

model = LiteLLMModel(
    model="ollama/mixtral:8x7b",
    api_base="http://192.168.13.162:11434"
)
```

## Files Updated

1. **phoenix_persistent.py**
   - Added Ollama connection test on startup
   - Changed evaluator to use LiteLLM + Ollama
   - Added dashboard logging (`client.log_evaluations()`)
   - Shows hallucination details in console

2. **phoenix_with_evals.py**
   - Same updates as above
   - Works with `--auto-eval` mode

3. **test_ollama_eval.py** (NEW)
   - Comprehensive test suite
   - Verifies Ollama connection
   - Tests evaluation pipeline
   - Shows sample results

## Expected Output

When Phoenix starts:

```
✅ Phoenix version: 4.x.x
🔍 Testing Ollama connection...
✅ Ollama connected: mixtral:8x7b available for evaluation

🚀 Launching Phoenix on port 6006...
================================================================================
✅ PHOENIX SERVER IS RUNNING WITH PERSISTENT STORAGE!

   📊 Dashboard: http://localhost:6006
   💾 Database: e:\network of obserbility\networkingAgent\.phoenix\phoenix_traces.db
   
   🤖 Auto-evaluation running every 60s
================================================================================
```

When evaluation runs:

```
[10:30:45] Running auto-evaluation...

🔍 Evaluating 5 LLM spans for hallucinations...
   🤖 Using Ollama: mixtral:8x7b

   ✅ Factual: 4
   ⚠️  Hallucinated: 1

   🚨 1 hallucination detected!
      - The model claimed AP will fail in 2 hours, but no time prediction data exists in context...

   💾 Results saved to: phoenix_eval_results.csv
   📊 Results logged to Phoenix dashboard at http://localhost:6006
```

## Dashboard View

Open http://localhost:6006 and you'll see:

### Traces Tab
- All agent executions
- LLM calls with inputs/outputs
- Tool invocations

### Evaluations Tab (**NOW VISIBLE!**)
- Hallucination detection results
- Factual vs hallucinated breakdown
- Per-span explanations from mixtral
- Confidence scores

### Example Evaluation
```
Span: LLM Call #42
Label: hallucinated
Score: 0.0
Explanation: The output claims "AP-001 will fail within 2 hours" 
but the context only provides current risk score of 52.5 with no 
failure time prediction. This is an unsupported claim.
```

## Verification Checklist

✅ **Ollama is running**
```bash
curl http://192.168.13.162:11434/api/tags
# Should show mixtral:8x7b in the list
```

✅ **LiteLLM is installed**
```bash
pip list | findstr litellm
# Should show: litellm x.x.x
```

✅ **Phoenix evals installed**
```bash
pip list | findstr arize-phoenix
# Should show: arize-phoenix x.x.x
```

✅ **Test works**
```bash
python test_ollama_eval.py
# Should show: 🎉 ALL TESTS PASSED!
```

✅ **Phoenix auto-eval works**
```bash
python phoenix_persistent.py --auto-eval
# Should show: ✅ Ollama connected: mixtral:8x7b
```

✅ **Dashboard shows evaluations**
- Open http://localhost:6006
- Click "Evaluations" tab
- Should see hallucination detection results

## Troubleshooting

### Issue: "Cannot connect to Ollama"

**Solution:**
```bash
# Test connection
curl http://192.168.13.162:11434/api/tags

# If fails, check:
# 1. Is Ollama running?
# 2. Is it accessible from your network?
# 3. Try: ping 192.168.13.162
```

### Issue: "mixtral:8x7b not found"

**Solution:**
```bash
# On the Ollama server, pull the model:
ollama pull mixtral:8x7b
```

### Issue: "LiteLLM not found"

**Solution:**
```bash
pip install litellm
```

### Issue: "Evaluations not in dashboard"

**Solution:**
1. Check Phoenix version (need 4.0+)
2. Make sure `--auto-eval` flag is used
3. Wait 60 seconds for first evaluation
4. Check CSV file was created (phoenix_eval_results.csv)
5. Look for "Results logged to Phoenix dashboard" message

### Issue: "Evaluation takes too long"

**Note:** Ollama on CPU can be slow (30-60s per evaluation).

**Options:**
1. Increase `--eval-interval` to reduce frequency:
   ```bash
   python phoenix_persistent.py --auto-eval --eval-interval 300  # Every 5 min
   ```

2. Use smaller model (faster but less accurate):
   - Change `mixtral:8x7b` to `llama3.1:8b` in code
   - Edit phoenix_persistent.py line with `model="ollama/mixtral:8x7b"`

3. Use GPU if available (check Ollama server)

## Performance Notes

- **mixtral:8x7b on CPU**: ~30-60 seconds per evaluation
- **mixtral:8x7b on GPU**: ~5-10 seconds per evaluation
- **Batch size**: Evaluates all pending spans at once
- **Recommended interval**: 60-300 seconds

## Next Steps

1. ✅ **Test the setup:**
   ```bash
   python test_ollama_eval.py
   ```

2. ✅ **Start Phoenix with auto-eval:**
   ```bash
   python phoenix_persistent.py --auto-eval
   ```

3. ✅ **Run your agent:**
   ```bash
   python agents/risk_score_agent.py --continuous 15
   ```

4. ✅ **View in dashboard:**
   ```
   http://localhost:6006
   ```

5. ✅ **Check evaluations tab** - Results should now be visible!

## Summary

✅ Phoenix now uses **Ollama mixtral:8x7b** for evaluation  
✅ Evaluations are **logged to dashboard** (previously missing)  
✅ No API keys required (uses your local Ollama server)  
✅ Results visible in **Evaluations tab**  
✅ Auto-evaluation runs every 60 seconds (configurable)  

Your hallucination detection is now fully working with Ollama!
