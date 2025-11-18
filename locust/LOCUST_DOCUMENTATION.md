# Locust Load Testing Documentation

## Overview
This project includes two Locust load testing configurations for testing the Mock Meraki API Server:

1. **`locustfile.py`** - Read-only API testing (GET endpoints)
2. **`locustfile_updates.py`** - Write/Update API testing (POST/PUT endpoints) with dynamic backoff

## Prerequisites

### Install Locust
```bash
pip install locust
```

### Start Mock Server
```bash
python mock_server.py
```
The server runs on `http://127.0.0.1:5000` by default.

## Configuration

### Environment Variables
```bash
# Organization and Network IDs
set ORG_ID=999781
set NETWORK_ID=L_3947405073390239794
set HOST=http://127.0.0.1:5000
```

### Inline Configuration (in files)
```python
ORG_ID = "999781"
NETWORK_ID = "L_3947405073390239794"
HOST = "http://127.0.0.1:5000"
```

## 1. Read-Only Testing (`locustfile.py`)

### Purpose
Tests GET endpoints to simulate read-heavy traffic patterns.

### Endpoints Tested
- `/` - Root endpoint
- `/organizations` - List organizations
- `/networks` - List networks
- `/networks/{id}/clients` - Network clients
- `/networks/{id}/traffic` - Network traffic
- `/networks/{id}/events` - Network events
- `/networks/{id}/settings` - Network settings
- `/networks/{id}/groupPolicies` - Group policies
- `/networks/{id}/appliance/connectivityMonitoringDestinations` - Connectivity monitoring
- `/networks/{id}/appliance/security/intrusion` - Security intrusion
- `/organizations/{id}/uplinks/statuses` - Uplink statuses
- `/organizations/{id}/appliance/vpn/stats` - VPN statistics

### Run Command
```bash
# Web UI
locust -f locustfile.py

# Headless mode
locust -f locustfile.py --headless -u 3 -r 1 --run-time 2m
```

## 2. Update Testing (`locustfile_updates.py`)

### Purpose
Tests POST/PUT endpoints to simulate write/update traffic with realistic networking problem scenarios and dynamic backoff.

### Key Features
- **Dynamic Backoff**: Wait time increases after successful updates to simulate system degradation
- **Realistic Payloads**: Simulates real-time networking problems (latency, packet loss, jitter)
- **Comprehensive Coverage**: Tests all major update endpoints

### Endpoints Tested

#### Appliance Settings
- **POST** `/networks/{id}/appliance/settings`
- **PUT** `/networks/{id}/appliance/settings`

**Payload Example:**
```json
{
  "latencyMs": 150,
  "packetLossPct": 2.5,
  "jitterMs": 15,
  "degradedLinks": [
    {"uplink": "wan1", "status": "degraded"},
    {"uplink": "wan2", "status": "ok"}
  ],
  "note": "auto-load-test-update"
}
```

#### Wireless Settings
- **POST** `/networks/{id}/wireless/settings`

**Payload Example:**
```json
{
  "latencyMs": 200,
  "packetLossPct": 1.8,
  "ssidHealth": {"poorClients": 12}
}
```

#### Network Settings
- **PUT** `/networks/{id}/settings`

**Payload Example:**
```json
{
  "latencyMs": 180,
  "trafficShaping": {"enabled": true}
}
```

#### Group Policies
- **PUT** `/networks/{id}/groupPolicies`

**Payload Example:**
```json
{
  "name": "dynamic-policy",
  "firewallAndTrafficShaping": {
    "settings": "custom",
    "l7Rules": [
      {"type": "deny", "value": "peer-to-peer"}
    ]
  }
}
```

#### Connectivity Monitoring
- **PUT** `/networks/{id}/appliance/connectivityMonitoringDestinations`

**Payload Example:**
```json
{
  "destinations": [
    {"description": "dns", "ip": "8.8.8.8"},
    {"description": "gateway", "ip": "192.168.1.1"}
  ]
}
```

#### Access Control Lists
- **PUT** `/networks/{id}/switch/accessControlLists`

**Payload Example:**
```json
{
  "rules": [
    {
      "comment": "block-bad-hosts",
      "policy": "deny",
      "protocol": "any",
      "srcCidr": "0.0.0.0/0",
      "destCidr": "10.10.10.10/32"
    }
  ]
}
```

#### Login Security
- **PUT** `/organizations/{id}/loginSecurity`

**Payload Example:**
```json
{
  "enforceTwoFactorAuth": true,
  "apiAccess": {"restricted": true}
}
```

#### Security Intrusion
- **PUT** `/networks/{id}/appliance/security/intrusion`

**Payload Example:**
```json
{
  "mode": "prevention",
  "rulesets": {"balanced": true}
}
```

### Dynamic Backoff Mechanism

The update testing implements a sophisticated backoff system:

1. **Base Wait Time**: 0.2-0.8 seconds between requests
2. **Success Bonus**: +0.2 seconds after each successful update (max 5.0 seconds)
3. **Failure Recovery**: -0.5 seconds after failed requests (min 0.0 seconds)
4. **Simulated Degradation**: As more updates succeed, the system appears to slow down

### Run Command
```bash
# Web UI
locust -f locustfile_updates.py

# Headless mode
locust -f locustfile_updates.py --headless -u 5 -r 1 --run-time 2m
```

## Testing Scenarios

### Scenario 1: Read-Only Load
```bash
locust -f locustfile.py --headless -u 10 -r 2 --run-time 5m
```
- 10 concurrent users
- 2 users spawned per second
- 5 minutes duration
- Tests GET endpoints only

### Scenario 2: Update Load with Degradation
```bash
locust -f locustfile_updates.py --headless -u 5 -r 1 --run-time 3m
```
- 5 concurrent users
- 1 user spawned per second
- 3 minutes duration
- Tests POST/PUT endpoints with dynamic backoff

### Scenario 3: Mixed Load Testing
```bash
# Terminal 1: Read testing
locust -f locustfile.py --headless -u 8 -r 1 --run-time 10m

# Terminal 2: Update testing
locust -f locustfile_updates.py --headless -u 3 -r 0.5 --run-time 10m
```

## Monitoring and Analysis

### Locust Web UI
- Open `http://localhost:8089` when running without `--headless`
- Real-time metrics and charts
- Download CSV reports

### Key Metrics to Monitor
- **Response Time**: Should increase over time with update testing
- **Request Rate**: Updates per second
- **Error Rate**: Failed requests
- **User Count**: Concurrent users

### Expected Behavior
1. **Initial Phase**: Fast response times
2. **Update Phase**: Response times increase after successful updates
3. **Degradation Phase**: System appears slower due to accumulated backoff
4. **Recovery**: Faster response times after failures

## Troubleshooting

### Common Issues

#### 1. "No module named 'locust'"
```bash
pip install locust
```

#### 2. "Connection refused"
- Ensure mock server is running: `python mock_server.py`
- Check HOST configuration in locust files

#### 3. "404 Not Found" errors
- Verify ORG_ID and NETWORK_ID are correct
- Check mock server logs for endpoint availability

#### 4. No dynamic backoff effect
- Ensure you're using `locustfile_updates.py`
- Check that updates are succeeding (200 status codes)
- Monitor the `dynamic_sleep_bonus` variable in logs

### Debug Mode
Add logging to see dynamic backoff in action:
```python
# In locustfile_updates.py, add to _apply_dynamic_sleep method:
print(f"Update result: {response_ok}, Bonus: {self.dynamic_sleep_bonus}")
```

## Performance Tuning

### Adjusting Backoff Parameters
```python
# In locustfile_updates.py
def _apply_dynamic_sleep(self, response_ok: bool):
    if response_ok:
        # Increase bonus amount
        self.dynamic_sleep_bonus = min(self.dynamic_sleep_bonus + 0.5, 10.0)
    else:
        # Adjust recovery rate
        self.dynamic_sleep_bonus = max(self.dynamic_sleep_bonus - 1.0, 0.0)
```

### Task Weights
Modify `@task(weight)` decorators to change endpoint frequency:
```python
@task(3)  # 3x more frequent
def post_appliance_settings(self):
    # ...

@task(1)  # 1x frequency
def put_security_intrusion(self):
    # ...
```

## Integration with CI/CD

### Automated Testing
```bash
# Run in CI pipeline
locust -f locustfile_updates.py --headless -u 10 -r 2 --run-time 5m --html=report.html
```

### Performance Baselines
- Establish baseline response times
- Set thresholds for acceptable degradation
- Alert on performance regressions

## Conclusion

This Locust testing setup provides comprehensive coverage of both read and write operations on the Mock Meraki API Server. The dynamic backoff mechanism in `locustfile_updates.py` realistically simulates how real systems degrade under update load, making it an excellent tool for:

- Performance testing
- Load testing
- Degradation scenario testing
- Capacity planning
- System behavior validation

Use the appropriate locust file based on your testing needs:
- **`locustfile.py`** for read-heavy scenarios
- **`locustfile_updates.py`** for update-heavy scenarios with degradation simulation
