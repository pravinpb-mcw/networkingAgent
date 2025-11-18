# Multi-Agent Network Monitoring System

## Overview

This system implements a **multi-agent architecture** for intelligent network monitoring and automated mitigation strategy generation. It uses the **tool calling pattern** where a supervisor agent (Network Monitor) orchestrates specialized worker agents (Mitigation Strategy Agent).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER                                      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│          NETWORK CHANGE DETECTION AGENT                      │
│              (Supervisor/Controller)                         │
│                                                              │
│  Responsibilities:                                           │
│  • Monitor network metrics continuously                      │
│  • Detect performance anomalies                              │
│  • Call Meraki API tools                                     │
│  • Send alerts via webhooks                                  │
│  • Orchestrate mitigation agent when needed                  │
│                                                              │
│  Tools Available:                                            │
│  • get_device_loss_and_latency_history                       │
│  • get_organization_uplinks_statuses                         │
│  • get_network_clients                                       │
│  • get_network_events                                        │
│  • send_network_alert                                        │
│  • generate_mitigation_strategy ← Subagent Tool              │
└────────────────────┬───────────────────┬────────────────────┘
                     │                   │
                     │ Normal Flow       │ Issue Detected
                     │                   │
                     ▼                   ▼
              ┌─────────────┐    ┌──────────────────────────┐
              │   Alert     │    │  Call Mitigation Agent   │
              │  Sent to    │    │        as Tool           │
              │  Webhook    │    └─────────┬────────────────┘
              └─────────────┘              │
                                           ▼
                     ┌─────────────────────────────────────────┐
                     │   MITIGATION STRATEGY AGENT             │
                     │      (Specialist/Worker)                │
                     │                                         │
                     │  Responsibilities:                      │
                     │  • Analyze issue context                │
                     │  • Review current configurations        │
                     │  • Generate detailed mitigation plans   │
                     │  • Provide actionable steps             │
                     │  • Include rollback procedures          │
                     │                                         │
                     │  Tools Available:                       │
                     │  • get_device_loss_and_latency_history  │
                     │  • get_organization_uplinks_statuses    │
                     │  • get_network_settings                 │
                     │  • get_connectivity_monitoring          │
                     │  • update_connectivity_monitoring       │
                     │  • update_uplink                        │
                     │  • update_appliance_settings            │
                     │  • get_access_control_lists             │
                     │  • get_security_intrusion               │
                     └────────────┬────────────────────────────┘
                                  │
                                  │ Returns mitigation strategy
                                  │
                                  ▼
                     ┌─────────────────────────────────────────┐
                     │  Network Monitor receives strategy       │
                     │  and includes it in alert message        │
                     └─────────────────────────────────────────┘
```

## Multi-Agent Pattern: Tool Calling

This system uses the **Tool Calling** pattern where:

1. **Controller Agent** (Network Monitor) maintains orchestration control
2. **Worker Agent** (Mitigation Strategy) is invoked as a tool
3. Worker agent doesn't interact with user directly
4. Results flow back to controller for final presentation

### Why Tool Calling Pattern?

- ✅ Centralized control and decision-making
- ✅ Clear separation of concerns
- ✅ Controller maintains conversation context
- ✅ Predictable workflow execution
- ✅ Easy to add more specialist agents

## Components

### 1. Network Change Detection Agent (`network_monitor_agent.py`)

**Role:** Main supervisor agent that monitors network health

**Capabilities:**
- Continuous monitoring of target device metrics
- Detection of latency, packet loss, jitter anomalies
- Uplink status monitoring
- Threshold-based alerting
- **Calls mitigation agent when issues detected**

**Thresholds:**
```python
{
    "latency_warning": 50.0,      # ms
    "latency_critical": 100.0,    # ms
    "loss_warning": 1.0,          # %
    "loss_critical": 3.0,         # %
    "jitter_warning": 10.0,       # ms
    "jitter_critical": 25.0       # ms
}
```

**Target Device:**
- Serial: `Q2MN-Q3J9-YJHW`
- Network: `L_3947405073390239794`

### 2. Mitigation Strategy Agent (`mitigation_strategy_agent.py`)

**Role:** Specialist agent for generating remediation strategies

**Capabilities:**
- Root cause analysis
- Configuration review
- Multi-phase mitigation planning
- Risk assessment
- Rollback procedure generation

**Output Structure:**
1. **Immediate Actions** (0-5 min) - Emergency stabilization
2. **Short-term Fixes** (5-30 min) - Configuration adjustments
3. **Investigation Steps** - Diagnostic procedures
4. **Long-term Solutions** (1-24 hrs) - Infrastructure improvements
5. **Preventive Measures** - Ongoing optimizations

## Integration Flow

### When Network Monitor Detects an Issue:

1. **Detection Phase**
   ```python
   # Network monitor checks metrics
   latency = 75.5 ms  # Exceeds warning threshold (50ms)
   packet_loss = 0.5%
   jitter = 15.3 ms
   ```

2. **Tool Call Phase**
   ```python
   # Network monitor calls mitigation agent as a tool
   await call_mitigation_agent(
       issue_type="High Latency",
       severity="warning",
       current_latency_ms=75.5,
       current_packet_loss_pct=0.5,
       current_jitter_ms=15.3,
       uplink_status="active",
       additional_context="Gradual increase over 30 minutes"
   )
   ```

3. **Strategy Generation Phase**
   ```python
   # Mitigation agent analyzes and generates strategy
   # - Reviews device history
   # - Checks uplink configuration
   # - Analyzes network settings
   # - Generates comprehensive mitigation plan
   ```

4. **Result Integration Phase**
   ```python
   # Network monitor receives strategy
   # Includes it in alert message
   await send_network_alert(
       title="Network Alert: High Latency",
       message=f"Issue detected\n\nMITIGATION STRATEGY:\n{strategy}",
       status="warning"
   )
   ```

## Usage

### Run Network Monitor (with Mitigation Capability)

```bash
# Single check
python network_monitor_agent.py

# Continuous monitoring (every 15 seconds)
python network_monitor_agent.py --continuous 15

# Continuous monitoring (every 5 minutes)
python network_monitor_agent.py --continuous 300
```

### Test Mitigation Agent Standalone

```bash
python mitigation_strategy_agent.py
```

### Run Multi-Agent Integration Tests

```bash
python test_multi_agent.py
```

## Configuration

### Environment Variables (`.env`)

```bash
# Required
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_key
ANTHROPIC_BASE_URL=https://api.z.ai/api/anthropic

# Optional - Webhooks for alerts
TEAMS_WEBHOOK_URL=your_teams_webhook
SLACK_WEBHOOK_URL=your_slack_webhook
```

### MCP Server Configuration (`mcp-inspector-config.json`)

Must include the Meraki MCP server configuration with all required tools.

## Example Scenarios

### Scenario 1: High Latency Warning

**Trigger:**
- Latency: 75ms (threshold: 50ms)

**Network Monitor Actions:**
1. Detects latency spike
2. Calls `generate_mitigation_strategy` tool
3. Receives comprehensive strategy
4. Sends alert with strategy to Teams/Slack

**Mitigation Strategy Includes:**
- Immediate: Check for bandwidth saturation
- Short-term: Adjust QoS settings
- Investigation: Review traffic patterns
- Long-term: Consider bandwidth upgrade
- Preventive: Set up trend alerts

### Scenario 2: Critical Packet Loss

**Trigger:**
- Packet Loss: 5% (threshold: 3%)

**Network Monitor Actions:**
1. Detects critical packet loss
2. Calls mitigation agent with severity='critical'
3. Receives urgent mitigation plan
4. Sends critical alert

**Mitigation Strategy Includes:**
- Immediate: Failover to backup uplink
- Short-term: Investigate physical connections
- Investigation: Check for DDoS or interference
- Long-term: Implement redundant paths
- Preventive: Enable proactive failover

### Scenario 3: Uplink Failure

**Trigger:**
- Uplink Status: 'failed'

**Network Monitor Actions:**
1. Detects uplink failure
2. Calls mitigation agent
3. Receives emergency procedures
4. Sends critical alert

**Mitigation Strategy Includes:**
- Immediate: Activate secondary uplink
- Short-term: Contact ISP support
- Investigation: Check cable/fiber integrity
- Long-term: Review SLA and redundancy
- Preventive: Set up automatic failover

## Tool Customization

### Adding Context to Mitigation Agent

The network monitor can pass rich context to the mitigation agent:

```python
@tool("generate_mitigation_strategy")
async def call_mitigation_agent(
    issue_type: str,
    severity: str,
    current_latency_ms: float,
    current_packet_loss_pct: float,
    current_jitter_ms: float,
    uplink_status: str = "unknown",
    additional_context: str = ""  # ← Rich context can be passed here
) -> str:
    # Agent processes context and generates strategy
    ...
```

### Customizing Output Format

The mitigation agent can be configured to return different formats:

- Detailed strategy (default)
- Executive summary
- Step-by-step checklist
- Configuration snippets
- Runbook format

## Benefits of This Architecture

### 1. Separation of Concerns
- Network monitoring logic separate from mitigation planning
- Each agent has focused, well-defined responsibilities
- Easier to test and maintain

### 2. Scalability
- Easy to add more specialist agents (e.g., SecurityAgent, CapacityAgent)
- Controller can orchestrate multiple specialists
- Agents can be updated independently

### 3. Context Engineering
- Mitigation agent receives only relevant context
- Prevents information overload
- Enables focused, high-quality strategies

### 4. Reusability
- Mitigation agent can be called by other systems
- Strategy generation logic is encapsulated
- Can be used standalone or as a tool

### 5. Maintainability
- Clear interfaces between agents
- Tool-based integration is well-documented
- Easy to add features to specific agents

## Testing

### Test Coverage

1. **Unit Tests**
   - Mitigation agent standalone
   - Network monitor standalone
   - Tool wrapper functionality

2. **Integration Tests**
   - Multi-agent communication
   - Context passing
   - Error handling

3. **End-to-End Tests**
   - Full monitoring cycle
   - Issue detection → mitigation → alert
   - Continuous monitoring

### Running Tests

```bash
# Run all tests
python test_multi_agent.py

# Test individual components
python mitigation_strategy_agent.py  # Standalone test
python network_monitor_agent.py      # Single check
```

## Troubleshooting

### Issue: Mitigation agent not called

**Check:**
- Are thresholds being exceeded?
- Is the tool properly registered?
- Check logs for tool invocation

### Issue: Strategy generation fails

**Check:**
- MCP server connectivity
- API credentials
- Tool permissions

### Issue: Context not passed correctly

**Check:**
- Tool parameter types
- Metric formatting
- Additional context string

## Future Enhancements

### Planned Features

1. **Security Analysis Agent**
   - Threat detection
   - Intrusion analysis
   - Security remediation

2. **Capacity Planning Agent**
   - Growth projections
   - Resource optimization
   - Upgrade recommendations

3. **Cost Optimization Agent**
   - Usage analysis
   - Cost-benefit analysis
   - Budget recommendations

4. **Handoff Pattern**
   - Allow agents to transfer control
   - Enable agent-to-agent conversations
   - User can interact with active agent

### Architecture Evolution

```
Current:  Network Monitor → (Tool) → Mitigation Agent
                                                ↓
Future:                                    Results

          Network Monitor → (Tool) → Mitigation Agent
                ↓                           ↓
           (Handoff)                    (Tool)
                ↓                           ↓
          Security Agent  →  (Tool)  → Cost Agent
```

## References

- [LangChain Multi-Agent Documentation](https://docs.langchain.com/multi-agent)
- [MCP Use Documentation](https://github.com/wong2/mcp-use)
- [Meraki API Documentation](https://developer.cisco.com/meraki/api-v1/)

## Support

For issues or questions:
1. Check the logs in console output
2. Review MCP server configuration
3. Verify environment variables
4. Test agents individually before integration
5. Check network connectivity to APIs

---

**Last Updated:** November 13, 2025
**Version:** 1.0.0
