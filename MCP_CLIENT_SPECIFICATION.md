# MCP Client Specification Document

## Executive Summary

This document provides a comprehensive specification for implementing an **Intelligent Network Orchestration Agent** similar to the existing MCP client. This specification can be used by LLMs, coding agents, or developers to recreate or extend the functionality in any programming language or framework.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture](#architecture)
3. [Core Components](#core-components)
4. [System Behavior](#system-behavior)
5. [API Integration](#api-integration)
6. [Tool Specifications](#tool-specifications)
7. [Configuration Management](#configuration-management)
8. [Execution Modes](#execution-modes)
9. [LLM Integration](#llm-integration)
10. [Error Handling](#error-handling)
11. [Output Format](#output-format)
12. [Implementation Guidelines](#implementation-guidelines)

---

## 1. System Overview

### Purpose
An AI-powered automated network management system that intelligently monitors, analyzes, and automatically fixes Cisco Meraki network issues using LLM integration and policy-driven decision-making.

### Key Characteristics
- **Autonomous**: Takes actions without human confirmation
- **Intelligent**: Uses LLM for decision-making and analysis
- **Conservative**: Only makes changes when actual problems exist
- **Policy-Driven**: Follows centralized policy files for routing decisions
- **Comprehensive**: Monitors all aspects of network health

### Technology Stack
- **Language**: Python 3.11+
- **LLM Provider**: Google Gemini (gemini-2.5-flash)
- **Framework**: mcp_use library for MCP integration
- **API**: Cisco Meraki REST API
- **Config Format**: JSON for MCP config, YAML/TXT for policies

---

## 2. Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     MCP Client Layer                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Interactive Chat / Automated Analysis / Uplink Mgmt │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           LLM Agent (Gemini 2.5 Flash)               │   │
│  │  - Natural Language Processing                       │   │
│  │  - Decision Making                                   │   │
│  │  - Policy Interpretation                             │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              MCP Agent Framework                      │   │
│  │  - Tool Orchestration                                │   │
│  │  - Memory Management                                 │   │
│  │  - Step Execution                                    │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                    MCP Server Layer                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                   MCP Tools                          │   │
│  │  • Monitoring Tools (get_*)                          │   │
│  │  • Automation Tools (update_*, create_*)             │   │
│  │  • Uplink Management (update_uplink)                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Meraki API / Mock Server                   │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  Cisco Meraki Cloud                          │
└─────────────────────────────────────────────────────────────┘
```

### Component Relationships

1. **User Interface Layer**: CLI-based interactive chat or automated modes
2. **LLM Layer**: Gemini LLM for intelligent decision-making
3. **Agent Layer**: MCP Agent for tool orchestration
4. **Tool Layer**: MCP Server tools for network operations
5. **API Layer**: Meraki REST API or Mock Server
6. **Network Layer**: Actual Cisco Meraki infrastructure

---

## 3. Core Components

### 3.1 MCP Client (`mcp_client.py`)

**Purpose**: Main orchestration agent that integrates LLM with MCP tools

**Key Functions**:
- `run_meraki_chat()` - Interactive chat mode
- `run_automated_analysis(phase)` - Phased network analysis
- `get_uplink_data_via_llm()` - Uplink management and rerouting
- `get_uplink_latency_monitoring()` - Latency-based uplink monitoring
- `test_connection()` - Connection testing and validation
- `get_common_system_prompt()` - System prompt generator

**Dependencies**:
```python
import asyncio
import logging
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
```

### 3.2 Configuration Manager (`config.py`)

**Purpose**: Centralized configuration management

**Key Components**:
```python
class Config:
    - meraki_config: API keys, network IDs, endpoints
    - llm_config: Model settings, temperature, tokens
    - server_config: Mock vs real API settings
```

**Environment Variables**:
- `GEMINI_API_KEY`: Google Gemini API key
- `MERAKI_API_KEY`: Cisco Meraki API key
- `NETWORK_ID`: Target network identifier
- `ORGANIZATION_ID`: Organization identifier
- `USE_MOCK`: Boolean for mock server usage

### 3.3 MCP Server Tools

**Purpose**: Individual tools for network operations

**Tool Categories**:

1. **Monitoring Tools** (Read-Only):
   - `get_organizations`
   - `get_organization_networks`
   - `get_organization_uplinks_statuses`
   - `get_network_settings`
   - `get_network_traffic`
   - `get_network_vpn_stats`
   - `get_network_events`
   - `get_network_clients`
   - `get_device_loss_and_latency_history`
   - `get_connectivity_monitoring_destinations`
   - `get_network_group_policies`
   - `get_network_access_control_lists`
   - `get_organization_login_security`
   - `get_network_security_intrusion`

2. **Automation Tools** (Write Operations):
   - `update_network_settings`
   - `update_uplink` (CORE UPLINK TOOL)
   - `update_appliance_settings`
   - `create_network_appliance_settings`
   - `create_network_wireless_settings`
   - `update_network_group_policy`
   - `create_organization_network`
   - `update_connectivity_monitoring_destinations`
   - `update_network_access_control_lists`
   - `update_organization_login_security`
   - `update_network_security_intrusion`

---

## 4. System Behavior

### 4.1 Core Behavioral Rules

**CRITICAL BEHAVIOR REQUIREMENTS**:

1. **Autonomous Operation**:
   - NEVER ask "Would you like me to proceed"
   - NEVER ask for user confirmation before taking action
   - Execute actions automatically when problems detected

2. **Conservative Decision-Making**:
   - ONLY make changes when ACTUAL network problems exist
   - NEVER make changes "just for the sake of making changes"
   - ONLY modify settings if it will improve network performance/security

3. **Clear Communication**:
   - ALWAYS provide clear reasoning for decisions
   - ALWAYS explain why changes were made or not made
   - Use structured output format (Analysis/Decision/Reasoning)

4. **Efficient Execution**:
   - Complete tasks in minimal steps (3-5 tool calls per phase)
   - Do NOT over-analyze
   - STOP after making decisions

5. **Comprehensive Problem Solving**:
   - FIX ALL detected problems, not just monitor them
   - Use actual fixing tools (update_*, create_*)
   - Retry empty tools or use alternative approaches
   - Continue until all issues are addressed

### 4.2 Decision-Making Framework

```
1. ANALYZE:
   - Thoroughly examine network data and metrics
   - Identify patterns, anomalies, and issues

2. EVALUATE:
   - Determine if there are ACTUAL problems or issues
   - Assess severity and impact
   - Check against policy guidelines

3. DECIDE:
   - Only make changes if problems exist
   - Never make suggestions or "improvements" without clear issues
   - Apply policy-driven rules for specific scenarios

4. EXPLAIN:
   - Always provide clear reasoning for decisions
   - Document what was checked
   - Explain why action was taken or not taken

5. EXECUTE:
   - If changes needed, use appropriate tools immediately
   - No confirmation requests
   - Monitor execution results

6. REPORT:
   - Document actions taken
   - Summarize changes made
   - Provide before/after states
```

---

## 5. API Integration

### 5.1 Meraki API Specifications

**Base URL**: `https://api.meraki.com/api/v1`

**Authentication**:
```
Headers:
  X-Cisco-Meraki-API-Key: <MERAKI_API_KEY>
  Content-Type: application/json
```

**Common Endpoints**:
```
GET  /organizations
GET  /organizations/{organizationId}/networks
GET  /organizations/{organizationId}/uplinks/statuses
GET  /networks/{networkId}/appliance/settings
GET  /networks/{networkId}/traffic
GET  /networks/{networkId}/vpnStats
GET  /networks/{networkId}/events
GET  /networks/{networkId}/clients
GET  /devices/{serial}/lossAndLatencyHistory

PUT  /networks/{networkId}/appliance/settings
PUT  /devices/{serial}/appliance/uplink
POST /organizations/{organizationId}/networks
```

### 5.2 Mock Server Specifications

**Purpose**: Testing environment without real API calls

**Base URL**: `http://127.0.0.1:8000`

**Features**:
- Simulates all Meraki API endpoints
- Returns realistic test data
- Allows testing of rerouting logic
- No API key required

---

## 6. Tool Specifications

### 6.1 Monitoring Tool Template

```python
Tool Name: get_<resource>
Purpose: Retrieve <resource> information
Method: GET
Endpoint: /api/v1/<resource>
Parameters:
  - organizationId (optional)
  - networkId (optional)
  - timespan (optional, default: 86400)
Returns:
  - JSON object or array of resource data
Error Handling:
  - Return empty array/object for "not found"
  - Return error message for API failures
```

### 6.2 Automation Tool Template

```python
Tool Name: update_<resource>
Purpose: Modify <resource> configuration
Method: PUT or POST
Endpoint: /api/v1/<resource>
Parameters:
  - organizationId or networkId (required)
  - Configuration object (varies by resource)
Returns:
  - Updated configuration object
  - Success/failure status
Error Handling:
  - Validate input parameters
  - Return detailed error messages
  - Rollback on failure if possible
```

### 6.3 Core Uplink Tool Specification

**Tool**: `update_uplink`

**Purpose**: Reroute devices between WAN uplinks

**Endpoint**: `PUT /devices/{serial}/appliance/uplink`

**Parameters**:
```json
{
  "serial": "Q2XX-XXXX-XXXX",
  "uplink": "wan1" | "wan2" | "wan3" | "wan4"
}
```

**Logic**:
1. Receive serial number and target uplink
2. Validate serial and uplink exist
3. Send PUT request to Meraki API
4. Return success/failure status
5. Log rerouting action

**Usage Example**:
```python
update_uplink(serial="Q2XX-1234-5678", uplink="wan2")
```

---

## 7. Configuration Management

### 7.1 MCP Configuration (`mcp-inspector-config.json`)

```json
{
  "mcpServers": {
    "meraki": {
      "command": "python",
      "args": ["server/meraki_server.py"],
      "env": {
        "MERAKI_API_KEY": "${MERAKI_API_KEY}",
        "NETWORK_ID": "${NETWORK_ID}",
        "ORGANIZATION_ID": "${ORGANIZATION_ID}"
      }
    }
  }
}
```

### 7.2 Environment Configuration (`.env`)

```ini
# API Keys
GEMINI_API_KEY=your_gemini_api_key
MERAKI_API_KEY=your_meraki_api_key

# Network Configuration
NETWORK_ID=L_123456789
ORGANIZATION_ID=123456
SERIAL=Q2XX-XXXX-XXXX

# Server Configuration
USE_MOCK=true
MOCK_BASE_URL=http://127.0.0.1:8000
BASE_URL=https://api.meraki.com/api/v1

# LLM Configuration
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512
```

### 7.3 Policy Configuration (`policy.txt`)

```text
NETWORK REROUTING UPLINK POLICIES
================================

1. WAN CAPACITY POLICY
   - Each WAN can handle maximum 20 devices
   - When a WAN exceeds 20 devices, reroute ONLY excess devices
   - Excess = devices beyond the 20-device limit

2. DOWN WAN POLICY
   - When a WAN is down (status != "active"):
     * Only reroute EXCESS devices (beyond 20)
     * Keep first 20 devices on the down WAN
     * Move excess to available WANs

3. WAN CREATION POLICY
   - If ALL WANs exceed 20 devices:
     * Create WAN3 (or next available WAN)
     * Reroute excess devices to new WAN

4. DEVICE DISTRIBUTION
   - Always distribute excess devices EQUALLY across available WANs
   - Round-robin distribution for fairness
```

---

## 8. Execution Modes

### 8.1 Interactive Chat Mode

**Command**: `python client/mcp_client.py`

**Features**:
- Natural language command input
- Predefined shortcuts (monitor, analyze, optimize, security, etc.)
- Real-time response streaming
- Conversation history management
- Tool inspection

**Shortcuts**:
- `monitor` - Comprehensive network monitoring
- `analyze` - AI-powered network analysis
- `optimize` - Automated optimization recommendations
- `security` - Security posture review
- `performance` - Network performance analysis
- `fix` - Automatic issue resolution
- `tools` - List available tools
- `clear` - Clear conversation history
- `exit`/`quit` - End session

### 8.2 Automated Analysis Mode

**Command**: `python client/mcp_client.py --automate [--phase=N]`

**Phases**:

**Phase 1: Organization Overview**
- Tools: `get_organizations`, `get_organization_networks`
- Focus: Organization structure, network count
- API Calls: 2-3

**Phase 2: Network Infrastructure**
- Tools: Uplinks, settings, traffic, VPN, latency, connectivity
- Focus: Infrastructure health, performance
- API Calls: 3-4
- Fixes: Uses `update_network_settings`, `create_network_appliance_settings`

**Phase 3: Security & Monitoring**
- Tools: Events, login security, intrusion detection, ACLs, clients
- Focus: Security vulnerabilities, unauthorized access
- API Calls: 3-4
- Fixes: Uses `update_network_access_control_lists`, `update_organization_login_security`

**Phase 4: Devices & Performance**
- Tools: Clients, latency history, connectivity, group policies
- Focus: Device issues, performance problems
- API Calls: 3-4
- Fixes: Uses `update_network_settings`, `update_network_group_policy`

**Phase 5: VPN & Advanced Performance**
- Tools: VPN stats, latency, settings, appliance, policies
- Focus: VPN performance, QoS optimization
- API Calls: 3-4
- Fixes: Uses `update_network_settings`, `create_network_appliance_settings`, `update_network_group_policy`

### 8.3 Uplink Management Mode

**Command**: `python client/mcp_client.py --uplink`

**Process**:
1. Load policy from `policy.txt`
2. Call `get_network_settings` - Check WAN status
3. Call `get_organization_uplinks_statuses` - Get device data
4. Count devices per WAN
5. Apply policy rules
6. If overloaded, create WAN3 via `update_appliance_settings`
7. Reroute excess devices via `update_uplink`
8. Report results (before/after state)

**Expected Output**:
```
**Analysis:**
- WAN1: 25 devices (overloaded by 5)
- WAN2: 15 devices (ok)

**Decision:**
- Reroute 5 excess devices from WAN1 to WAN2

**Execution:**
- Moving device Q2XX-XXXX-XXXX to WAN2
- Moving device Q2XX-XXXX-XXXX to WAN2
- ...

**Results:**
- BEFORE: WAN1=25, WAN2=15
- AFTER: WAN1=20, WAN2=20
- DEVICES MOVED: 5
```

### 8.4 Latency-Based Uplink Mode

**Command**: `python client/mcp_client.py --uplink-through-latency`

**Process**:
1. Load latency policy from `latency_policy.yaml` or `latency_policy.txt`
2. Get appliance settings for latency data
3. Get uplink statuses for device data
4. Apply latency-based rerouting rules
5. Reroute devices based on latency thresholds
6. Report rerouting results

**Latency Policy Example** (`latency_policy.yaml`):
```yaml
latency_thresholds:
  critical: 150  # ms
  high: 100      # ms
  medium: 70     # ms
  low: 0         # ms

rerouting_rules:
  critical: 3    # Use 3 WANs
  high: 2        # Use 2 WANs
  medium: 2      # Use 2 WANs
  low: 0         # No action
```

---

## 9. LLM Integration

### 9.1 LLM Configuration

**Model**: `gemini-2.5-flash`

**Settings**:
```python
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    google_api_key=gemini_api_key,
    temperature=0.1,        # Low for consistency
    max_tokens=512,         # Reduced for quota management
    request_timeout=30,     # 30 second timeout
    retry_on_failure=True   # Enable automatic retries
)
```

**Why Gemini Flash**:
- Higher free tier limits (15 RPM, 1 million TPM)
- Lower latency than Pro
- Good balance of cost and performance
- Suitable for network automation tasks

### 9.2 System Prompt Structure

**Components**:

1. **Role Definition**:
   ```
   You are an AUTOMATED NETWORK ORCHESTRATION AGENT with 
   INTELLIGENT DECISION-MAKING capabilities.
   ```

2. **Critical Behavior Rules**:
   - Never ask for confirmation
   - Only make changes for actual problems
   - Always explain reasoning
   - Use structured output format

3. **Output Format Requirements**:
   ```
   **Analysis:**
   [Analysis text]
   
   **Decision:**
   [Decision text]
   
   **Reasoning:**
   [Reasoning text]
   ```

4. **Decision-Making Framework**:
   - ANALYZE → EVALUATE → DECIDE → EXPLAIN → EXECUTE → REPORT

5. **Domain Expertise**:
   - Network orchestration
   - Cisco Meraki management
   - Performance monitoring
   - Security automation

6. **Execution Requirements**:
   - Fix ALL detected problems
   - Use actual fixing tools
   - Comprehensive problem solving
   - Stop after making decisions

### 9.3 Agent Configuration

```python
agent = MCPAgent(
    llm=llm,
    client=client,
    max_steps=10,           # Maximum tool calls per request
    memory_enabled=False,   # Disable for simplicity
    verbose=False           # Disable for clean output
)
```

**Parameters**:
- `max_steps`: 10-75 depending on mode (higher for comprehensive analysis)
- `memory_enabled`: False to reduce complexity and token usage
- `verbose`: False to hide "Thought:" and "Final Answer:" prefixes

---

## 10. Error Handling

### 10.1 API Error Handling

**Error Types**:

1. **503 Service Unavailable (Model Overloaded)**:
   - Retry with exponential backoff (5s, 10s, 20s)
   - Max retries: 3
   - Inform user to wait before retrying

2. **429 Too Many Requests (Quota Exceeded)**:
   - No retries
   - Inform user of quota limits
   - Suggest waiting 55 seconds or upgrading

3. **finish_reason Errors (API Compatibility)**:
   - Known Gemini API issue
   - Continue execution despite error
   - Log warning but treat as success

4. **Empty Responses**:
   - Valid response indicating no data
   - Report as "no data found", not "tool failed"
   - Continue to next tool

5. **Network Errors**:
   - Retry once after 2 seconds
   - Log error details
   - Return error message to user

### 10.2 Validation

**Input Validation**:
- Check for required environment variables
- Validate network IDs and serial numbers
- Verify API keys before execution

**Output Validation**:
- Verify tool responses are valid JSON
- Check for expected fields
- Log warnings for unexpected data

### 10.3 Logging

**Log Levels**:
- ERROR: API failures, critical issues
- WARNING: Missing configuration, empty responses
- INFO: Successful operations, phase completions
- DEBUG: Detailed execution flow (disabled by default)

**Log Format**:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Specific Loggers**:
- `mcp_use`: Set to ERROR level (too verbose)
- `mcp_use.agent`: Set to ERROR level
- `mcp_use.client`: Set to ERROR level

---

## 11. Output Format

### 11.1 Standard Response Format

**Required Structure**:
```
**Analysis:**
[Detailed analysis of network data, metrics, patterns]

**Decision:**
[Clear statement of what action will be taken or not taken]

**Reasoning:**
[Explanation of why this decision was made]

[Optional: Additional sections for execution details]
```

### 11.2 Comprehensive Analysis Format

```
============================================================
✅ PHASE N COMPLETE
============================================================
**Analysis:**
[Analysis text]

**Decision:**
[Decision text]

**Reasoning:**
[Reasoning text]

**Report:**
- **Checked:** [What was examined]
- **Decisions Made:** [Actions taken]
- **Reasoning:** [Why actions were taken]
- **NO CHANGES NEEDED.** [Only if no changes]
```

### 11.3 Uplink Rerouting Format

```
**POLICY FILE:**
[Policy content]

**Analysis:**
- WAN1: X devices (status)
- WAN2: Y devices (status)

**Decision:**
- [What will be done]

**Execution:**
- Moving device [serial] to [WAN]
- ...

**Results:**
- BEFORE: WAN1=X, WAN2=Y
- AFTER: WAN1=A, WAN2=B
- DEVICES MOVED: N
```

---

## 12. Implementation Guidelines

### 12.1 Technology Requirements

**Required Libraries**:
```
langchain-google-genai>=2.0.0
mcp-use>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
fastapi>=0.104.0 (for mock server)
uvicorn>=0.24.0 (for mock server)
pyyaml>=6.0.1 (for policy parsing)
```

**Python Version**: 3.11 or higher

**API Keys**:
- Google Gemini API key (free tier available)
- Cisco Meraki API key (dashboard.meraki.com)

### 12.2 Project Structure

```
networkingAgent/
├── client/
│   ├── __init__.py
│   └── mcp_client.py          # Main client implementation
├── server/
│   ├── __init__.py
│   ├── meraki_server.py       # Mock Meraki API
│   ├── meraki_client.py       # API client wrapper
│   ├── get_*.py               # Monitoring tools
│   ├── update_*.py            # Automation tools
│   └── create_*.py            # Creation tools
├── mock_data/
│   └── comprehensive_api_data.json  # Test data
├── config.py                  # Configuration management
├── policy.txt                 # Uplink routing policies
├── latency_policy.yaml        # Latency-based policies
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── mcp-inspector-config.json  # MCP server configuration
└── README.md                  # Documentation
```

### 12.3 Implementation Steps

**Phase 1: Setup & Configuration**
1. Create project structure
2. Set up environment variables
3. Install dependencies
4. Configure MCP server

**Phase 2: Core Components**
1. Implement configuration manager
2. Create MCP client wrapper
3. Build system prompt generator
4. Set up LLM integration

**Phase 3: Tool Development**
1. Implement monitoring tools (get_*)
2. Implement automation tools (update_*, create_*)
3. Create mock server for testing
4. Test each tool individually

**Phase 4: Execution Modes**
1. Implement interactive chat mode
2. Build automated analysis phases
3. Create uplink management mode
4. Add latency-based monitoring

**Phase 5: Testing & Refinement**
1. Test with mock server
2. Test with real Meraki API
3. Refine LLM prompts
4. Optimize API usage and quotas

### 12.4 Best Practices

**LLM Integration**:
- Use low temperature (0.0-0.1) for consistency
- Implement retry logic with exponential backoff
- Monitor API quotas and usage
- Use minimal max_tokens to reduce costs

**Network Operations**:
- Always validate input before API calls
- Test with mock server first
- Implement rollback mechanisms for critical changes
- Log all network modifications

**Error Handling**:
- Never fail silently
- Provide clear error messages
- Implement retry logic for transient errors
- Log errors for debugging

**Performance**:
- Minimize API calls (phased analysis)
- Cache responses when appropriate
- Use async operations where possible
- Implement rate limiting

**Security**:
- Never commit API keys to version control
- Use environment variables for sensitive data
- Validate all input parameters
- Implement audit logging for changes

### 12.5 Testing Strategy

**Unit Tests**:
- Test each tool individually
- Mock API responses
- Verify input validation
- Check error handling

**Integration Tests**:
- Test full execution flows
- Use mock server
- Verify tool orchestration
- Check policy application

**End-to-End Tests**:
- Test with real API (non-production)
- Verify actual network changes
- Validate rollback mechanisms
- Performance and quota testing

### 12.6 Deployment Considerations

**Production Deployment**:
- Use real Meraki API key
- Implement proper logging
- Set up monitoring and alerts
- Use production-grade error handling

**Scaling**:
- Consider multi-organization support
- Implement parallel execution for multiple networks
- Use job queues for long-running tasks
- Add database for audit trail

**Monitoring**:
- Track API usage and quotas
- Monitor LLM token consumption
- Log all network changes
- Alert on failures

---

## 13. Example Implementations

### 13.1 Basic MCP Client

```python
import asyncio
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient

load_dotenv()

async def main():
    # Create MCP client
    client = MCPClient.from_config_file("mcp-inspector-config.json")
    
    # Create LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=os.getenv("GEMINI_API_KEY"),
        temperature=0.1,
        max_tokens=512
    )
    
    # Create agent
    agent = MCPAgent(
        llm=llm,
        client=client,
        max_steps=10,
        memory_enabled=False,
        verbose=False
    )
    
    # Run query
    response = await agent.run("Check network status")
    print(response)
    
    # Cleanup
    await client.close_all_sessions()

if __name__ == "__main__":
    asyncio.run(main())
```

### 13.2 Uplink Rerouting Implementation

```python
async def uplink_rerouting():
    # Load policy
    with open('policy.txt', 'r') as f:
        policy = f.read()
    
    # Create prompt
    prompt = f"""
    UPLINK REROUTING TASK
    
    POLICY:
    {policy}
    
    STEPS:
    1. Get WAN status using get_network_settings
    2. Get device data using get_organization_uplinks_statuses
    3. Count devices per WAN
    4. Apply policy rules
    5. Reroute excess devices using update_uplink
    6. Report results
    
    EXECUTE NOW.
    """
    
    # Run agent
    response = await agent.run(prompt)
    print(response)
```

### 13.3 Phased Analysis Implementation

```python
async def run_phase(phase_num):
    phase_prompts = {
        1: "Phase 1: Check organizations and networks",
        2: "Phase 2: Check infrastructure and performance",
        3: "Phase 3: Check security and monitoring",
        4: "Phase 4: Check devices and performance",
        5: "Phase 5: Check VPN and advanced performance"
    }
    
    prompt = f"""
    {system_prompt}
    
    {phase_prompts[phase_num]}
    
    Execute this phase only. Be efficient (3-5 tool calls).
    """
    
    response = await agent.run(prompt)
    print(f"Phase {phase_num} Complete:")
    print(response)
    
    # Wait between phases
    if phase_num < 5:
        await asyncio.sleep(30)
```

---

## 14. Appendix

### A. Environment Variables Reference

```ini
# Required
GEMINI_API_KEY=           # Google Gemini API key
MERAKI_API_KEY=           # Cisco Meraki API key
NETWORK_ID=               # Target network ID
ORGANIZATION_ID=          # Organization ID

# Optional
USE_MOCK=false            # Use mock server (true/false)
MOCK_BASE_URL=            # Mock server URL
BASE_URL=                 # Real API base URL
LLM_MODEL=                # LLM model name
LLM_TEMPERATURE=0.1       # LLM temperature (0.0-1.0)
LLM_MAX_TOKENS=512        # Max tokens per request
SERIAL=                   # Device serial number
TIMESPAN=86400            # Data timespan in seconds
```

### B. Common Error Messages

| Error | Cause | Solution |
|-------|-------|----------|
| "GEMINI_API_KEY not found" | Missing environment variable | Set GEMINI_API_KEY in .env |
| "503 Service Unavailable" | Gemini model overloaded | Wait and retry, or use different model |
| "429 Too Many Requests" | API quota exceeded | Wait 55 seconds or upgrade plan |
| "finish_reason error" | Gemini API compatibility | Ignore warning, execution likely succeeded |
| "Empty response" | No data available | Normal for healthy networks |

### C. Policy File Examples

**Basic Uplink Policy**:
```text
WAN CAPACITY: 20 devices per WAN
EXCESS HANDLING: Reroute only excess devices
DOWN WAN: Keep first 20, reroute excess
WAN CREATION: Create WAN3 if all WANs > 20
DISTRIBUTION: Equal distribution across WANs
```

**Latency Policy**:
```yaml
thresholds:
  critical: 150
  high: 100
  medium: 70
  low: 0

actions:
  critical: use_3_wans
  high: use_2_wans
  medium: use_2_wans
  low: no_action
```

### D. API Rate Limits

**Gemini API (Free Tier)**:
- 15 requests per minute
- 1 million tokens per minute
- 1,500 requests per day

**Meraki API**:
- 5 requests per second per organization
- No daily limits on most endpoints
- Some endpoints have specific limits

**Quota Management**:
- Use phased analysis to reduce API calls
- Implement delays between phases (30 seconds)
- Monitor usage in Google Cloud Console
- Consider upgrading for production use

---

## Conclusion

This specification provides a complete blueprint for implementing an Intelligent Network Orchestration Agent. It covers all aspects from architecture and configuration to implementation details and best practices.

### Key Takeaways:

1. **Autonomous Operation**: The system must operate without human confirmation
2. **Conservative Approach**: Only make changes for actual problems
3. **Policy-Driven**: All routing decisions follow centralized policies
4. **LLM Integration**: Use Gemini for intelligent decision-making
5. **Comprehensive Monitoring**: Check all aspects of network health
6. **Efficient Execution**: Minimize API calls through phased analysis
7. **Clear Communication**: Always explain reasoning for decisions

### Next Steps for Implementation:

1. Set up development environment
2. Implement core configuration management
3. Create MCP client with LLM integration
4. Build and test individual tools
5. Implement execution modes
6. Test with mock server
7. Deploy to production with real API

Use this specification as a reference throughout the implementation process. Each section can be implemented independently, making it easy to build incrementally and test along the way.

