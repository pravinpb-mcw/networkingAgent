# Network Change Detection Agent

An intelligent MCP-based agent that continuously monitors your network for changes and automatically sends alerts to Microsoft Teams and Slack.

## 🎯 Overview

The Network Change Detection Agent uses the Model Context Protocol (MCP) to:
- **Monitor network performance** metrics (latency, packet loss, jitter, goodput)
- **Detect uplink status changes** (active, connecting, failed)
- **Track client connectivity** (online/offline status)
- **Send automatic alerts** to Teams/Slack when issues are detected
- **Provide intelligent analysis** using AI-powered decision making

## 🚀 Features

### Real-Time Monitoring
- Continuous network performance monitoring
- Automatic threshold-based alerting
- Uplink health tracking
- Client connectivity monitoring

### Webhook Integration
- **Microsoft Teams** integration via incoming webhooks
- **Slack** integration via incoming webhooks
- Formatted alert messages with metrics and status
- Multi-platform broadcasting

### AI-Powered Analysis
- Intelligent change detection
- Context-aware alerting (avoid alert fatigue)
- Detailed problem descriptions
- Actionable recommendations

## 📋 Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   pip install aiohttp asyncio python-dotenv langchain-google-genai mcp-use requests
   ```

2. **MCP Server** running (Meraki MCP server with webhook tools)

3. **Mock Server** (for testing):
   ```bash
   python mock_server.py
   ```

4. **Environment Variables** in `.env`:
   ```env
   # Gemini API Key (required)
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Webhook URLs (at least one required)
   TEAMS_WEBHOOK_URL=https://your-team.webhook.office.com/...
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
   ```

## 🔧 Setup

### 1. Configure Webhooks

#### Microsoft Teams:
1. Go to your Teams channel
2. Click "..." → "Connectors" → "Incoming Webhook"
3. Click "Configure", give it a name
4. Copy the webhook URL
5. Add to `.env` as `TEAMS_WEBHOOK_URL`

#### Slack:
1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks"
4. Add webhook to workspace
5. Copy the webhook URL
6. Add to `.env` as `SLACK_WEBHOOK_URL`

### 2. Verify Environment

```bash
# Check .env file has required variables
cat .env | grep -E "(GEMINI_API_KEY|TEAMS_WEBHOOK_URL|SLACK_WEBHOOK_URL)"

# Ensure MCP server config exists
ls mcp-inspector-config.json
```

### 3. Start Required Services

```bash
# Terminal 1: Start mock server
python mock_server.py

# Terminal 2: Ready to run agent
# (see usage below)
```

## 📊 Usage

### Single Check Mode

Perform a one-time network check:

```bash
python network_monitor_agent.py
```

**Output:**
```
🔍 Performing single network check...
============================================================

📊 MONITORING RESULT:
------------------------------------------------------------
Current Status: NORMAL
Metrics Summary: All metrics within normal range
Issues Detected: None
Alert Sent: No alerts needed
Recommendation: Network is healthy
------------------------------------------------------------
```

### Continuous Monitoring Mode

Run continuous monitoring with custom interval:

```bash
# Monitor every 60 seconds (default)
python network_monitor_agent.py --continuous

# Monitor every 30 seconds
python network_monitor_agent.py --continuous 30

# Monitor every 5 minutes
python network_monitor_agent.py --continuous 300
```

**Output:**
```
🚀 Starting continuous network monitoring (interval: 60s)
============================================================

============================================================
Monitoring Iteration #1 - 2025-11-13 12:30:00
============================================================

🔍 Checking network state for changes...
✅ Network check complete

📊 MONITORING RESULT:
------------------------------------------------------------
[Agent analysis and alerts]
------------------------------------------------------------

⏳ Waiting 60 seconds until next check...
```

### Help

```bash
python network_monitor_agent.py --help
```

## 🎯 Alert Thresholds

The agent uses the following thresholds:

### Latency
- **Normal**: < 50ms
- **Warning**: 50-100ms → Sends warning alert
- **Critical**: > 100ms → Sends critical alert

### Packet Loss
- **Normal**: < 1%
- **Warning**: 1-3% → Sends warning alert
- **Critical**: > 3% → Sends critical alert

### Jitter
- **Normal**: < 10ms
- **Warning**: 10-25ms → Sends warning alert
- **Critical**: > 25ms → Sends critical alert

### Goodput
- **Normal**: > 80%
- **Warning**: 70-80% → Sends warning alert
- **Critical**: < 70% → Sends critical alert

### Uplink Status
- **Active**: Normal
- **Connecting**: Warning → Sends warning alert
- **Failed**: Critical → Sends critical alert

## 📧 Alert Format

Alerts sent to Teams/Slack include:

```
Network Alert: [Issue Type]
Timestamp: 2025-11-13 12:30:45

ISSUE: High latency detected on network

CURRENT METRICS:
- Latency: 120.5ms (Threshold: 50ms) ⚠️
- Packet Loss: 0.8% (Threshold: 1%)
- Jitter: 8.2ms (Threshold: 10ms)
- Uplink Status: active

SEVERITY: WARNING

DETAILS:
Network latency has exceeded warning threshold (50ms).
Current latency is 120.5ms, which is 141% above baseline.
This may impact application performance and user experience.

RECOMMENDATION:
- Check uplink bandwidth utilization
- Review traffic patterns for congestion
- Consider QoS policy adjustments
```

## 🧪 Testing with Failure Simulations

Use the failure simulation scripts to test alert functionality:

### Test Gradual Degradation

```bash
# Terminal 1: Start continuous monitoring
python network_monitor_agent.py --continuous 10

# Terminal 2: Simulate gradual failure
python simulate_gradual_failure.py
```

**Expected Behavior:**
- Agent detects increasing latency around step 10-15
- Warning alert sent when latency exceeds 50ms
- Critical alert sent when latency exceeds 100ms
- Additional alerts for packet loss and jitter

### Test Instant Failure

```bash
# Terminal 1: Start continuous monitoring
python network_monitor_agent.py --continuous 10

# Terminal 2: Trigger instant failure
python simulate_instant_failure.py
```

**Expected Behavior:**
- Agent immediately detects critical state
- Critical alert sent with all metrics failing
- Uplink failure detected and alerted
- Comprehensive alert with full details

### Test Recovery

```bash
# After a failure simulation:
python restore_network.py

# Agent will detect recovery and may send recovery notification
```

## 🔍 Customization

### Adjust Thresholds

Edit `network_monitor_agent.py`:

```python
self.thresholds = {
    "latency_warning": 50.0,      # Change to your preference
    "latency_critical": 100.0,
    "loss_warning": 1.0,
    "loss_critical": 3.0,
    "jitter_warning": 10.0,
    "jitter_critical": 25.0,
    "goodput_warning": 80.0,
    "goodput_critical": 70.0
}
```

### Change Monitoring Interval

```python
# Default: 60 seconds
await detector.continuous_monitoring(interval_seconds=60)

# Custom: 30 seconds
await detector.continuous_monitoring(interval_seconds=30)

# Custom: 5 minutes
await detector.continuous_monitoring(interval_seconds=300)
```

### Modify Alert Messages

Edit the prompt in `get_monitoring_prompt()` method to customize:
- Alert format
- Alert content
- Severity levels
- Recommendations

## 🛠️ Advanced Features

### Webhook Tool Integration

The agent uses MCP webhook tools that can be called from any MCP client:

```python
# From Python code
from server.webhook_tool import send_network_alert

result = send_network_alert(
    title="Network Alert: High Latency",
    message="Latency exceeded threshold",
    status="warning",
    metrics={"latency_ms": 120.5, "loss_percent": 0.8},
    alerts=["High latency detected"]
)
```

### MCP Server Integration

The webhook tools are available in the MCP server:

```json
{
  "name": "send_network_alert",
  "description": "Send network alert to all configured webhooks",
  "parameters": {
    "title": "string",
    "message": "string",
    "status": "normal|warning|critical|error",
    "metrics": "object (optional)",
    "alerts": "array (optional)"
  }
}
```

## 📝 Logging

Logs are written to console with the following levels:

- **INFO**: Normal operations, monitoring iterations
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures, exceptions

Example log output:
```
2025-11-13 12:30:00 - network-monitor-agent - INFO - 🔍 Checking network state for changes...
2025-11-13 12:30:05 - network-monitor-agent - INFO - ✅ Network check complete
2025-11-13 12:30:05 - network-monitor-agent - INFO - ⏳ Waiting 60 seconds until next check...
```

## 🐛 Troubleshooting

### No Alerts Being Sent

**Problem**: Agent runs but no alerts appear in Teams/Slack

**Solutions**:
1. Verify webhook URLs in `.env`:
   ```bash
   echo $TEAMS_WEBHOOK_URL
   echo $SLACK_WEBHOOK_URL
   ```

2. Test webhooks manually:
   ```bash
   python -c "from webhook_module import WebhookModule; w = WebhookModule(); print(w.is_configured())"
   ```

3. Check webhook module logs:
   ```bash
   python network_monitor_agent.py | grep webhook
   ```

### Agent Not Detecting Changes

**Problem**: Simulations run but agent doesn't detect issues

**Solutions**:
1. Verify MCP server is running with webhook tools
2. Check agent can access network data:
   ```bash
   curl http://127.0.0.1:5000/devices/lossAndLatencyHistory
   ```

3. Reduce monitoring interval for faster detection:
   ```bash
   python network_monitor_agent.py --continuous 10
   ```

### High CPU/Memory Usage

**Problem**: Agent consuming too many resources

**Solutions**:
1. Increase monitoring interval:
   ```bash
   python network_monitor_agent.py --continuous 300  # 5 minutes
   ```

2. Reduce agent max_steps:
   ```python
   self.agent = MCPAgent(
       llm=self.llm,
       client=self.client,
       max_steps=10,  # Reduce from 15
       memory_enabled=False,  # Disable memory
       verbose=False
   )
   ```

## 🔐 Security Notes

- **Webhook URLs** contain sensitive authentication tokens
- Store in `.env` file, never commit to git
- Use environment variables in production
- Rotate webhooks periodically
- Limit webhook scope to specific channels

## 📚 Related Documentation

- **Webhook Module**: `webhook_module.py`
- **Failure Simulations**: `SIMULATION_README.md`
- **MCP Client**: `MCP_CLIENT_SPECIFICATION.md`
- **MCP Server**: `server/meraki_server.py`

## 🎯 Use Cases

### Production Monitoring
Run continuously on a server to monitor production networks:
```bash
nohup python network_monitor_agent.py --continuous 60 > monitor.log 2>&1 &
```

### Development Testing
Use with simulations during development:
```bash
# Terminal 1: Monitoring
python network_monitor_agent.py --continuous 10

# Terminal 2: Simulate issues
python simulate_gradual_failure.py
```

### Incident Response
Run single checks during troubleshooting:
```bash
python network_monitor_agent.py
```

### Scheduled Checks
Add to cron for periodic monitoring:
```cron
*/5 * * * * cd /path/to/project && python network_monitor_agent.py
```

---

**🚀 Start monitoring your network with intelligent AI-powered alerts!**
