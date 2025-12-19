# Phoenix Observability System

Professional observability and validation system for AI agent monitoring.

## 📁 Folder Structure

```
phoenix/
├── server.py                    # Main Phoenix server with auto-evaluation
├── VALIDATION_GUIDE.md          # Complete validation documentation
├── .phoenix_data/               # Phoenix database and traces
│   └── phoenix_traces.db        # SQLite database
├── validators/                  # Validation modules
│   ├── tool_validators.py       # Tool parameter validation
│   ├── comprehensive_validators.py  # Math & hallucination detection
│   ├── input_output_validators.py   # Input-output consistency
│   └── README.md                # Validator documentation
└── utils/                       # Utility scripts
    ├── check_math_failures.py   # Debug math validation
    ├── check_risk_math.py       # Verify risk calculations
    └── check_tool_params.py     # Check parameter completeness
```

## 🚀 Quick Start

### Start Phoenix Server
```bash
# From networkingAgent/ directory
start_phoenix.bat

# Or manually:
python phoenix\server.py --auto-eval --eval-interval 10
```

### Access Dashboard
```
http://localhost:6006
```

## ✅ Validation System

Phoenix runs 5 deterministic validators every 10 seconds:

### 1. **Tool Parameters Complete** (μ 1.00)
- Validates all required parameters present
- File: `validators/tool_validators.py`
- Checks: Missing params, None values, empty strings

### 2. **Input-Output Consistency** (μ 1.00)
- Cross-validates INPUT matches OUTPUT
- File: `validators/input_output_validators.py`
- Checks: AP serial consistency, network ID, risk range, metrics

### 3. **LLM Decision Completeness** (μ 1.00)
- Validates workflow steps followed
- File: `validators/tool_validators.py`
- Checks: Agent 1/2/3 workflows, tool call sequences

### 4. **AP Exists in Topology** (μ 1.00)
- Verifies APs exist in real network
- File: `validators/comprehensive_validators.py`
- Checks: `comprehensive_api_data.json` topology

### 5. **Risk Math Verification** (μ 1.00)
- Recalculates risk scores independently
- File: `validators/comprehensive_validators.py`
- Checks: `agent_data/risk_scores.json` metrics

## 🔧 Configuration

### Server Settings
- **Host**: `0.0.0.0` (accessible from network)
- **Port**: `6006`
- **Auto-Eval**: Enabled
- **Eval Interval**: 10 seconds

### Data Sources
- **Topology**: `../mock_data/comprehensive_api_data.json`
- **Risk Scores**: `../agent_data/risk_scores.json`
- **Policies**: `../policies/network_policy.json`

### Database
- **Location**: `phoenix/.phoenix_data/phoenix_traces.db`
- **Type**: SQLite (persistent storage)

## 🛠️ Utility Scripts

### Check Math Validation
```bash
python phoenix\utils\check_risk_math.py
```
Shows risk calculation verification for all APs.

### Check Tool Parameters
```bash
python phoenix\utils\check_tool_params.py
```
Lists which tools are validated and which are missing.

### Debug Failures
```bash
python phoenix\utils\check_math_failures.py
```
Queries Phoenix database for evaluation failures.

## 📊 Validation Results

All validators target **μ 1.00 (100%)**:

| Validator | Pass Rate | Purpose |
|-----------|-----------|---------|
| tool_parameters_complete | μ 1.00 | No missing params |
| input_output_consistency | μ 1.00 | No hallucinated data |
| llm_decision_completeness | μ 1.00 | Workflow followed |
| ap_exists_in_topology | μ 1.00 | No fake devices |
| risk_math_verification | μ 1.00 | Math correct |

## 📖 Documentation

- **Validation Guide**: `VALIDATION_GUIDE.md` - Complete explanation for clients
- **Validator README**: `validators/README.md` - Best validator practices
- **Server Code**: `server.py` - Full implementation with comments

## 🔄 Auto-Evaluation Flow

```
1. Agent runs → Phoenix traces captured
2. Wait 10 seconds (eval interval)
3. Wait 2 seconds (file write buffer)
4. Run all 5 validators
5. Log results to Phoenix dashboard
6. Display μ scores in UI
7. Repeat every 10 seconds
```

## 🎯 Integration

Phoenix is integrated with:
- **Agent 1** (Risk Calculation)
- **Agent 2** (Nearest AP Finder)
- **Agent 3** (Failover Suggestion)
- **MCP Server** (Tool calls)

All traces automatically captured and validated.

## 🚨 Troubleshooting

### Database Empty
Delete `.phoenix_data/phoenix_traces.db` and restart server.

### Low Pass Rates
- Check file writes completed (`time.sleep(2)`)
- Verify tools in `TOOL_REQUIRED_PARAMS`
- Check metrics in `risk_scores.json`

### Import Errors
Ensure validators folder in path:
```python
sys.path.insert(0, str(Path(__file__).parent / "validators"))
```

## 📝 License

Part of Network Observability Agent (NOA) project.
