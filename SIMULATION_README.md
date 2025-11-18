# Network Failure Simulation Suite

A comprehensive suite of Python scripts to simulate various network failure scenarios for testing your network monitoring and orchestration agent.

## 📋 Overview

This simulation suite provides realistic network failure scenarios to test how your MCP-based network orchestration agent responds to:

- **Gradual Network Degradation**: Simulates slow deterioration of network performance over time
- **Instantaneous Network Failure**: Simulates catastrophic sudden failures (fiber cut, power loss, etc.)
- **Network Restoration**: Restores network to healthy baseline state

## 🚀 Quick Start

### Prerequisites

1. **Python 3.8+** with asyncio and aiohttp
2. **Mock Meraki Server** running on `http://127.0.0.1:5000`
3. **Comprehensive API data** in `mock_data/comprehensive_api_data.json`

### Installation

```bash
# Install required packages
pip install aiohttp asyncio
```

### Running the Simulation Manager

The easiest way to run simulations is through the manager script:

```bash
python failure_simulation_manager.py
```

This provides an interactive menu with options to:
1. Run gradual failure simulation
2. Run instantaneous failure simulation
3. Restore network to healthy state
4. View current network state
5. Exit

## 📊 Available Simulations

### 1. Gradual Network Failure

**Script**: `simulate_gradual_failure.py`

**Duration**: 5 minutes (configurable)

**What it does**:
- Progressively degrades network metrics over 30 steps
- Updates every 10 seconds
- Simulates realistic slow network deterioration

**Metrics affected**:
- **Latency**: 15ms → 500ms
- **Packet Loss**: 0.1% → 10%
- **Jitter**: 1ms → 50ms
- **Goodput**: 95% → 45%
- **Uplink Status**: active → connecting → failed
- **Client Status**: Online → progressively Offline
- **VPN Tunnels**: Active → Down

**Usage**:
```bash
python simulate_gradual_failure.py
```

**Example Output**:
```
📊 Progress: 33.3% | Elapsed: 100.0s
------------------------------------------------------------
✅ Step 10/30: Appliance Settings Updated
   └─ Latency: 176.67ms, Loss: 3.4%, Jitter: 17.23ms
   └─ WAN1: active, WAN2: active

✅ Step 10/30: Device History Updated
   └─ Latency: 176.67ms, Loss: 3.4%, Goodput: 78.3%

✅ Step 10/30: Client Statuses Updated
   └─ Online: 4, Offline: 1
```

### 2. Instantaneous Network Failure

**Script**: `simulate_instant_failure.py`

**Duration**: Immediate (< 5 seconds)

**What it does**:
- Triggers immediate catastrophic network failure
- Simulates events like fiber cuts, power loss, DDoS attacks
- All metrics immediately become critical

**Metrics affected**:
- **Latency**: → 1500ms (unreachable)
- **Packet Loss**: → 100% (total loss)
- **Jitter**: → 250ms (extreme)
- **Goodput**: → 0%
- **All Uplinks**: → FAILED
- **All Clients**: → OFFLINE
- **All VPN Tunnels**: → DOWN
- **Critical Events**: Logged

**Usage**:
```bash
python simulate_instant_failure.py
```

**Safety Feature**: Requires user confirmation before executing

**Example Output**:
```
💥 TRIGGERING INSTANTANEOUS NETWORK FAILURE
============================================================
⚠️  WARNING: This will cause COMPLETE NETWORK OUTAGE
============================================================

Triggering failure in 3...
Triggering failure in 2...
Triggering failure in 1...

🚨 FAILURE TRIGGERED!

💥 APPLIANCE FAILURE TRIGGERED!
   └─ Latency: 1500.0ms (CRITICAL)
   └─ Packet Loss: 100.0% (TOTAL LOSS)
   └─ Jitter: 250.0ms (EXTREME)
   └─ WAN1: FAILED
   └─ WAN2: FAILED

💥 ALL CLIENTS OFFLINE!
   └─ Total Clients Affected: 5
   └─ Online: 0
   └─ Offline: 5
```

### 3. Network Restoration

**Script**: `restore_network.py`

**Duration**: Immediate (< 5 seconds)

**What it does**:
- Restores all network metrics to healthy baseline values
- Clears critical events
- Brings network back to operational state

**Restoration actions**:
- Sets latency to 15.5ms
- Sets packet loss to 0.1%
- Sets jitter to 1.2ms
- Sets goodput to 95%
- Activates all uplinks
- Brings clients back online
- Restores VPN tunnels
- Clears critical events

**Usage**:
```bash
python restore_network.py
```

**Example Output**:
```
🔄 STARTING NETWORK RESTORATION
============================================================

✅ APPLIANCE SETTINGS RESTORED
   └─ Latency: 15.5ms
   └─ Packet Loss: 0.1%
   └─ Jitter: 1.2ms
   └─ WAN1: active
   └─ WAN2: active

✅ CLIENT STATUSES RESTORED
   └─ Online: 3
   └─ Offline: 2

✅ UPLINK STATUSES RESTORED
   └─ Active Uplinks: 1
   └─ Status: ALL ACTIVE

============================================================
✅ Network Restoration Complete!
============================================================
```

## 🔧 Configuration

### Modifying Simulation Parameters

Edit the configuration at the top of each script:

```python
# In simulate_gradual_failure.py
TOTAL_DURATION_SECONDS = 300  # Change to adjust simulation length
UPDATE_INTERVAL_SECONDS = 10   # Change update frequency
STEPS = TOTAL_DURATION_SECONDS // UPDATE_INTERVAL_SECONDS

# In simulate_instant_failure.py
FAILURE_METRICS = {
    "latencyMs": 1500.0,      # Adjust failure severity
    "packetLossPct": 100.0,
    "jitterMs": 250.0,
    "goodput": 0.0
}

# In restore_network.py
HEALTHY_METRICS = {
    "latencyMs": 15.5,        # Adjust healthy baseline
    "packetLossPct": 0.1,
    "jitterMs": 1.2,
    "goodput": 95.0
}
```

### Network Configuration

Adjust these to match your test environment:

```python
MOCK_SERVER_URL = "http://127.0.0.1:5000"
NETWORK_ID = "L_3947405073390239794"
ORGANIZATION_ID = "999781"
DEVICE_SERIAL = "Q2MN-Q3J9-YJHW"
```

## 📈 Monitoring the Simulations

### View Current Network State

Use the manager's option 4 or directly view the data:

```bash
# View comprehensive API data
cat mock_data/comprehensive_api_data.json | jq '.networks."L_3947405073390239794"'

# View device history
cat mock_data/comprehensive_api_data.json | jq '.device_loss_and_latency_history."Q2MN-Q3J9-YJHW" | .[-5:]'

# View uplink statuses
cat mock_data/comprehensive_api_data.json | jq '.organization_uplinks_statuses."999781"'
```

### Test with MCP Client

After starting a simulation, test your orchestration agent:

```bash
# Run automated analysis
python client/mcp_client.py --automate

# Run specific phase
python client/mcp_client.py --automate --phase 2

# Monitor uplinks
python client/mcp_client.py --uplink

# Monitor latency
python client/mcp_client.py --uplink-through-latency
```

## 🧪 Testing Scenarios

### Scenario 1: Gradual Degradation Detection

**Objective**: Test if your agent detects slow network degradation

```bash
# 1. Start with healthy network
python restore_network.py

# 2. Run gradual failure
python simulate_gradual_failure.py

# 3. Monitor with agent (in another terminal)
python client/mcp_client.py --automate --phase 2

# 4. Check if agent detected and responded
```

**Expected Behavior**:
- Agent should detect increasing latency around step 10-15
- Agent should trigger alerts when packet loss exceeds 2%
- Agent should attempt remediation when uplinks degrade

### Scenario 2: Instant Failure Response

**Objective**: Test if your agent responds to catastrophic failure

```bash
# 1. Start with healthy network
python restore_network.py

# 2. Trigger instant failure
python simulate_instant_failure.py

# 3. Monitor with agent (in another terminal)
python client/mcp_client.py --automate

# 4. Verify agent response
```

**Expected Behavior**:
- Agent should immediately detect critical state
- Agent should log critical events
- Agent should attempt failover or emergency measures

### Scenario 3: Recovery Verification

**Objective**: Test if your agent detects recovery

```bash
# 1. Run a failure simulation
python simulate_instant_failure.py

# 2. Verify agent detects failure
python client/mcp_client.py --automate --phase 2

# 3. Restore network
python restore_network.py

# 4. Verify agent detects recovery
python client/mcp_client.py --automate --phase 2
```

**Expected Behavior**:
- Agent should detect metrics returning to healthy state
- Agent should clear alerts
- Agent should log recovery event

## 🔍 Troubleshooting

### Mock Server Not Running

**Error**: `Connection refused to http://127.0.0.1:5000`

**Solution**:
```bash
# Start the mock server
python mock_server.py
```

### Data File Not Found

**Error**: `FileNotFoundError: mock_data/comprehensive_api_data.json`

**Solution**:
```bash
# Make sure mock server has generated data
# Or copy from existing backup
cp mock_data/backup/comprehensive_api_data.json mock_data/
```

### Permission Issues

**Error**: `PermissionError: cannot write to mock_data/`

**Solution**:
```bash
# Fix permissions
chmod +w mock_data/comprehensive_api_data.json
chmod +x simulate_*.py restore_network.py failure_simulation_manager.py
```

### Python Dependencies

**Error**: `ModuleNotFoundError: No module named 'aiohttp'`

**Solution**:
```bash
pip install aiohttp asyncio
```

## 📊 Understanding the Metrics

### Latency (ms)
- **Healthy**: 10-30ms
- **Acceptable**: 30-100ms
- **Degraded**: 100-200ms
- **Critical**: 200ms+
- **Failed**: 500ms+

### Packet Loss (%)
- **Healthy**: < 0.5%
- **Acceptable**: 0.5-1%
- **Degraded**: 1-3%
- **Critical**: 3-5%
- **Failed**: 5%+

### Jitter (ms)
- **Healthy**: < 5ms
- **Acceptable**: 5-15ms
- **Degraded**: 15-30ms
- **Critical**: 30ms+
- **Failed**: 50ms+

### Goodput (%)
- **Healthy**: 90-100%
- **Acceptable**: 80-90%
- **Degraded**: 70-80%
- **Critical**: 50-70%
- **Failed**: < 50%

## 🤝 Integration with MCP Client

The simulations are designed to work with your MCP client's automated analysis:

```python
# In your MCP client
async def run_automated_analysis(phase=None):
    """Run automated network analysis"""
    # ... your code ...
    
    # The simulation scripts update the same data structure
    # that your MCP client reads from the mock server
```

## 📝 Best Practices

1. **Always restore** after testing: Run `restore_network.py` after each simulation
2. **Monitor during simulation**: Run MCP client analysis in parallel to see real-time response
3. **Document findings**: Keep notes on how your agent responds to each scenario
4. **Adjust thresholds**: Tune your agent's alert thresholds based on simulation results
5. **Test iteratively**: Start with gradual failure, then test instant failure

## 🎯 Next Steps

1. **Run the manager**: `python failure_simulation_manager.py`
2. **Test gradual failure**: See how your agent handles slow degradation
3. **Test instant failure**: See how your agent handles catastrophic failure
4. **Analyze results**: Review agent logs and decisions
5. **Tune your agent**: Adjust thresholds and responses based on findings

## 📚 Additional Resources

- **MCP Client Documentation**: See `MCP_CLIENT_SPECIFICATION.md`
- **Mock Server Documentation**: See `mock_server.py` header comments
- **Network Monitoring Guide**: See `NOA-SPEC.md`

## ⚠️ Safety Notes

- These scripts modify `mock_data/comprehensive_api_data.json`
- Always keep a backup of your data file
- Don't run on production systems
- Use with mock server only, not real Meraki API

---

**Happy Testing! 🚀**
