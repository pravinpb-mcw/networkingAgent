# Phoenix Observability Guide for Risk Score Agent

## Overview
Arize Phoenix is now integrated into the Risk Score Agent for LLM tracing and observability.

## What You Can See in Phoenix

Phoenix provides visibility into:
- **LLM Calls**: Every interaction with Claude (prompts, responses, tokens)
- **Tool Executions**: MCP tool calls (latency data, usage history, clients)
- **Agent Flow**: Complete execution trace showing the workflow
- **Performance**: Latency, token usage, cost tracking
- **Errors**: Runtime exceptions and failures
- **Prompt Templates**: Actual prompts sent to the LLM

## Installation

1. **Install dependencies:**
   ```bash
   cd networkingAgent
   pip install -r requirements.txt
   ```

   This installs:
   - `arize-phoenix>=4.0.0` - Core Phoenix library
   - `openinference-instrumentation-langchain>=0.1.0` - LangChain auto-instrumentation
   - `opentelemetry-sdk>=1.20.0` - OpenTelemetry SDK
   - `opentelemetry-exporter-otlp>=1.20.0` - OTLP exporter

## Running with Phoenix Tracing

### Option 1: Run Agent with Phoenix (Recommended)

```bash
# Single calculation with Phoenix
python agents\risk_score_agent.py

# Continuous mode with Phoenix (every 10 seconds)
python agents\risk_score_agent.py --continuous 10

# Custom Phoenix port
python agents\risk_score_agent.py --phoenix-port 6007

# Disable Phoenix if needed
python agents\risk_score_agent.py --no-phoenix
```

Phoenix UI automatically launches at: **http://localhost:6006**

### Option 2: Use Batch Scripts

```bash
# Run risk agent with default settings (includes Phoenix)
run_agent1_risk.bat

# Or run all agents (Phoenix on agent 1 only)
run_all_agents.bat
```

## Viewing Traces in Phoenix

### Step 1: Start the Agent
```bash
python agents\risk_score_agent.py --continuous 10
```

You'll see:
```
================================================================================
🔍 PHOENIX OBSERVABILITY UI: http://localhost:6006
================================================================================

✅ Phoenix UI launched at: http://localhost:6006
✅ LangChain instrumentation enabled
```

### Step 2: Open Phoenix UI
Open your browser to: **http://localhost:6006**

### Step 3: Explore the Traces

#### Main Dashboard
- **Traces List**: Shows all agent executions
- **Spans**: Individual steps (LLM calls, tool calls)
- **Latency**: Time taken for each operation
- **Token Count**: Tokens used per LLM call

#### Trace View
Click on any trace to see:
1. **Execution Flow**: Visual tree of operations
   - Agent invocation
   - Tool calls (get_network_topology, get_wireless_latency_history, etc.)
   - LLM reasoning
   - JSON storage updates

2. **LLM Spans**: 
   - Model used (claude-sonnet-4)
   - Input prompt (full prompt sent)
   - Output response
   - Token usage (input/output)
   - Latency

3. **Tool Spans**:
   - Tool name (e.g., `get_wireless_latency_history`)
   - Input parameters
   - Output data
   - Execution time

4. **Attributes**:
   - Session ID
   - Network ID
   - Context data

### Step 4: Analyze Performance

#### Filter Traces
```python
# In Phoenix UI or using the Python API
import phoenix as px

# Get all LLM calls
llm_spans = px.active_session().get_spans_dataframe('span_kind == "LLM"')
print(llm_spans[['name', 'latency_ms', 'token_count']])

# Get all tool calls
tool_spans = px.active_session().get_spans_dataframe('span_kind == "TOOL"')
print(tool_spans[['name', 'latency_ms']])
```

#### Common Queries
- **Slow operations**: Sort by latency
- **Expensive calls**: Sort by token count
- **Errors**: Filter by status == ERROR
- **Specific tool**: Filter by tool name

## Verifying Tracing Works

### Quick Verification Test

1. **Start the agent:**
   ```bash
   python agents\risk_score_agent.py
   ```

2. **Check console output:**
   ```
   ✅ Phoenix UI launched at: http://localhost:6006
   ✅ LangChain instrumentation enabled
   🔍 Phoenix tracing is ACTIVE - View traces at: http://localhost:6006
   ```

3. **Open Phoenix UI:** http://localhost:6006

4. **Wait for agent to complete** (10-30 seconds)

5. **In Phoenix UI, you should see:**
   - At least 1 trace in the traces list
   - Multiple spans (LLM calls, tool calls)
   - Latency data for each span
   - Token usage for LLM calls

6. **Click on a trace to verify:**
   - ✅ See the execution tree
   - ✅ See LLM prompts and responses
   - ✅ See tool calls with parameters
   - ✅ See timing data

### Expected Trace Structure

A typical Risk Score Agent trace should show:

```
Trace: Agent Invocation
├─ LLM Call: Initial planning
├─ Tool: get_network_topology_link_layer
│  └─ Returns: AP list
├─ LLM Call: Process topology
├─ Tool: get_wireless_latency_history (AP 1)
├─ Tool: get_wireless_usage_history (AP 1)
├─ Tool: get_device_clients (AP 1)
├─ ... (repeat for each AP)
├─ LLM Call: Calculate risk scores
├─ Tool: update_risk_score (AP 1)
├─ ... (repeat for each AP)
└─ LLM Call: Final summary
```

## Troubleshooting

### Phoenix UI Not Loading

**Problem:** http://localhost:6006 doesn't open

**Solutions:**
1. Check if Phoenix started:
   ```bash
   # Look for this in console output:
   ✅ Phoenix UI launched at: http://localhost:6006
   ```

2. Check port availability:
   ```bash
   netstat -ano | findstr :6006
   ```

3. Try different port:
   ```bash
   python agents\risk_score_agent.py --phoenix-port 6007
   ```

### No Traces Appearing

**Problem:** Phoenix UI opens but no traces shown

**Solutions:**
1. Verify instrumentation is active:
   ```
   ✅ LangChain instrumentation enabled
   🔍 Phoenix tracing is ACTIVE
   ```

2. Run agent and wait for completion

3. Refresh Phoenix UI browser page

4. Check agent completed without errors

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'phoenix'`

**Solution:**
```bash
cd networkingAgent
pip install -r requirements.txt
```

**Problem:** `ModuleNotFoundError: No module named 'openinference'`

**Solution:**
```bash
pip install openinference-instrumentation-langchain opentelemetry-sdk opentelemetry-exporter-otlp
```

## Advanced Usage

### Export Traces for Analysis

```python
import phoenix as px

# Get active session
session = px.active_session()

# Export all traces as DataFrame
df = session.get_spans_dataframe()
df.to_csv('risk_agent_traces.csv')

# Filter and analyze
llm_calls = df[df['span_kind'] == 'LLM']
print(f"Total LLM calls: {len(llm_calls)}")
print(f"Average latency: {llm_calls['latency_ms'].mean():.2f}ms")
print(f"Total tokens: {llm_calls['token_count'].sum()}")
```

### Run LLM Evaluations

```python
from phoenix.evals import run_evals

# Evaluate retrieval quality
evals_df = run_evals(
    dataframe=df,
    evaluators=['relevance', 'hallucination'],
    model='gpt-4'
)
```

### Compare Multiple Runs

1. Run agent multiple times
2. In Phoenix UI, compare traces side-by-side
3. Identify performance differences
4. Optimize prompts or tool usage

## Integration with Other Agents

Phoenix is currently integrated with:
- ✅ **Risk Score Agent (Agent 1)**

To add to other agents:
1. Add import: `from phoenix_tracing import initialize_phoenix`
2. Call before agent init: `initialize_phoenix(ui_port=6007)`  # Use different port
3. Enable instrumentation

## Command Reference

```bash
# Basic usage
python agents\risk_score_agent.py

# Continuous with Phoenix
python agents\risk_score_agent.py --continuous 10

# Custom ports
python agents\risk_score_agent.py --phoenix-port 6007 --a2a-port 5001

# Disable Phoenix
python agents\risk_score_agent.py --no-phoenix

# Help
python agents\risk_score_agent.py --help
```

## URLs

- **Phoenix UI**: http://localhost:6006
- **Phoenix Docs**: https://docs.arize.com/phoenix
- **Phoenix GitHub**: https://github.com/Arize-ai/phoenix

## Next Steps

1. ✅ Run the risk agent and verify traces appear
2. Explore trace details in Phoenix UI
3. Monitor token usage and costs
4. Identify slow operations
5. Optimize prompts based on observations
6. Add Phoenix to other agents (Agent 2, 3, etc.)
