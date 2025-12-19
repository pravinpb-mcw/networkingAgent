# Risk Score Calculation Script

## Overview

This is a **standalone risk calculation script** that extracts the mathematical logic from Agent 1 into a pure Python tool.

**NO LLM | NO MCP CALLS | PURE CALCULATION ONLY**

## What It Does

Takes AP metrics as input → Applies scoring thresholds → Calculates weighted risk score → Returns classification

## Formula

```
RISK_SCORE = 0.25×latency + 0.20×jitter + 0.20×retrans + 0.15×snr + 0.10×load + 0.10×auth
```

## Scoring Thresholds

| Metric | Good (20) | Warning (50) | Critical (80) | Severe (100) |
|--------|-----------|--------------|---------------|--------------|
| Latency | < 30ms | 30-60ms | 60-100ms | > 100ms |
| Jitter | < 10ms | 10-20ms | 20-30ms | > 30ms |
| Retrans | < 20/min | 20-35/min | 35-50/min | > 50/min |
| SNR | > 25dB | 20-25dB | 15-20dB | < 15dB |
| Clients | < 20 | 20-40 | 40-60 | > 60 |
| Auth Fail | < 3/hr | 3-8/hr | 8-15/hr | > 15/hr |

## Risk Classifications

- **0-20**: 🟢 Stable Network
- **21-40**: 🟡 Temporary Degradation
- **41-70**: 🟠 Sustained Degradation
- **71-100**: 🔴 Likely Failure

## Usage

### 1. As a Command-Line Tool

#### Single AP with full metrics:
```bash
python calculate_risk_score.py \
  --ap-serial Q2XX-ABCD-1234 \
  --ap-name "AP-01" \
  --latency 45 \
  --jitter 15 \
  --retrans 30 \
  --snr 22 \
  --clients 15 \
  --auth-failures 2 \
  --pretty
```

#### Single AP with partial metrics (missing = default 20):
```bash
python calculate_risk_score.py \
  --ap-serial Q2XX-ABCD-1234 \
  --latency 80 \
  --retrans 55 \
  --summary
```

#### Batch processing from JSON:
```bash
python calculate_risk_score.py \
  --batch example_batch_input.json \
  --output risk_results.json \
  --pretty
```

### 2. As a Python Module

```python
from calculate_risk_score import calculate_ap_risk_score

# Calculate risk for a single AP
result = calculate_ap_risk_score(
    ap_serial="Q2XX-ABCD-1234",
    ap_name="AP-01",
    latency_ms=45.5,
    jitter_ms=15.2,
    retrans_per_min=30,
    snr_db=22.5,
    client_count=15,
    auth_failures_per_hour=2
)

print(f"Risk Score: {result['risk_score']}")
print(f"Classification: {result['risk_classification']}")
print(f"Indicator: {result['risk_indicator']}")
```

### 3. Batch Processing

```python
from calculate_risk_score import calculate_multiple_aps

ap_metrics_list = [
    {
        "ap_serial": "Q2XX-ABCD-1234",
        "latency_ms": 45,
        "retrans_per_min": 30,
        "snr_db": 22
    },
    {
        "ap_serial": "Q2XX-EFGH-5678",
        "latency_ms": 85,
        "retrans_per_min": 55,
        "snr_db": 18
    }
]

results = calculate_multiple_aps(ap_metrics_list)
for ap_serial, ap_result in results['results'].items():
    print(f"{ap_result['risk_indicator']} {ap_serial}: {ap_result['risk_score']}")
```

## Integration with New Agent

Your new agent should:

1. **Get all APs** using MCP tools (e.g., `get_wireless_health`, `get_network_topology_link_layer`)
2. **For each AP**, fetch metrics using MCP tools:
   - `get_wireless_latency_history` → latency, jitter
   - `get_wireless_usage_history` → retransmissions, SNR
   - `get_device_clients` → client count
3. **Call this script** with the metrics
4. **Store results** in JSON for all APs

### Example Integration:

```python
# In your new agent

# Step 1: Get all APs
aps = await mcp_client.call_tool("get_wireless_health", {...})

# Step 2 & 3: For each AP, fetch metrics and calculate risk
for ap in aps:
    # Fetch metrics
    latency_data = await mcp_client.call_tool("get_wireless_latency_history", 
                                               {"device_serial": ap["serial"]})
    usage_data = await mcp_client.call_tool("get_wireless_usage_history",
                                             {"device_serial": ap["serial"]})
    clients_data = await mcp_client.call_tool("get_device_clients",
                                               {"device_serial": ap["serial"]})
    
    # Calculate risk using this script
    from calculate_risk_score import calculate_ap_risk_score
    
    risk_result = calculate_ap_risk_score(
        ap_serial=ap["serial"],
        ap_name=ap["name"],
        latency_ms=latency_data.get("avg"),
        retrans_per_min=usage_data.get("retransmissionsPerMinute"),
        snr_db=usage_data.get("avgSignalToNoise"),
        client_count=len(clients_data)
    )
    
    # Step 4: Store in JSON
    store_risk_score(ap["serial"], risk_result)
```

## Output Format

### Single AP Output:
```json
{
  "success": true,
  "ap_serial": "Q2XX-ABCD-1234",
  "ap_name": "AP-01",
  "risk_score": 42.5,
  "risk_classification": "Sustained Degradation",
  "risk_indicator": "🟠",
  "timestamp": "2025-12-19T10:30:00Z",
  "metrics": {
    "latency_ms": 45.5,
    "latency_score": 50.0,
    "jitter_ms": 15.2,
    "jitter_score": 50.0,
    "retrans_per_min": 30,
    "retrans_score": 50.0,
    "snr_db": 22.5,
    "snr_score": 50.0,
    "client_count": 15,
    "load_score": 20.0,
    "auth_failures_per_hour": 2,
    "auth_score": 20.0
  },
  "calculation": {
    "formula": "0.25×lat + 0.20×jit + 0.20×ret + 0.15×snr + 0.10×load + 0.10×auth",
    "breakdown": {
      "latency_contribution": 12.5,
      "jitter_contribution": 10.0,
      "retrans_contribution": 10.0,
      "snr_contribution": 7.5,
      "load_contribution": 2.0,
      "auth_contribution": 2.0
    }
  }
}
```

## Testing

```bash
# Test with example data
cd networkingAgent/scripts
python calculate_risk_score.py --batch example_batch_input.json --pretty

# Quick test
python calculate_risk_score.py --ap-serial TEST-AP --latency 100 --summary
```

## Benefits

✅ **Pure Calculation** - No dependencies on LLM or MCP  
✅ **Reusable** - Can be called from any agent or script  
✅ **Consistent** - Same formula as Agent 1, guaranteed  
✅ **Fast** - Instant calculation, no API calls  
✅ **Testable** - Easy to unit test and validate  
✅ **Flexible** - CLI or module import  

## Notes

- **Missing metrics default to score 20** (assume okay when no data)
- All calculations use the exact formula from Agent 1
- Timestamps are in ISO 8601 UTC format
- Can process single AP or batch of APs
- Output is JSON for easy integration
