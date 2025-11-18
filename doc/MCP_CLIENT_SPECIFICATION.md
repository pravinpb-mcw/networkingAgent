# MCP Client Specification for Network Orchestration Agent

## Overview

This specification document provides a comprehensive blueprint for implementing an MCP (Model Context Protocol) client system that integrates LLM capabilities with network management tools. The system is designed for intelligent network orchestration and automation, specifically for Cisco Meraki network management.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM Client    │    │   MCP Client     │    │  Network API    │
│  (Google Gemini)│◄──►│  (mcp_use)       │◄──►│ (Meraki/Mock)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐            │
         └──────────────►│  Configuration   │◄───────────┘
                        │   Management     │
                        └──────────────────┘
```

## Core Components

### 1. Configuration Management (`config.py`)

#### Required Environment Variables
```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key
MERAKI_API_KEY=your_meraki_api_key

# Network Configuration
NETWORK_ID=your_network_id
ORGANIZATION_ID=your_organization_id
SERIAL=your_device_serial

# Service Configuration
USE_MOCK=false                    # Use mock server for testing
BASE_URL=https://api.meraki.com/api/v1
MOCK_BASE_URL=http://127.0.0.1:8000

# LLM Configuration
LLM_MODEL=gemini-2.5-flash
LLM_TEMPERATURE=0.1
LLM_MAX_TOKENS=512

# Monitoring
TIMESPAN=86400                    # Default time span in seconds
```

#### Configuration Class Structure
```python
class Config:
    def __init__(self):
        load_dotenv()
        self.validate_config()
    
    # Properties for all environment variables
    # Validation methods
    def get_mcp_config(self) -> Dict[str, Any]
```

### 2. MCP Client Implementation (`client/mcp_client.py`)

#### Core Dependencies
```python
from langchain_google_genai import ChatGoogleGenerativeAI
from mcp_use import MCPAgent, MCPClient
import asyncio
import json
import logging
from pathlib import Path
```

#### Main Agent Class Structure
```python
class NetworkOrchestrationAgent:
    def __init__(self):
        self.config = config
        self.client = None
        self.agent = None
        self.llm = None
    
    async def initialize(self):
        """Initialize MCP client and LLM"""
        
    def get_system_prompt(self) -> str:
        """Generate system prompt for LLM"""
        
    async def run_interactive_chat(self):
        """Interactive chat mode"""
        
    async def run_automated_analysis(self, phase: Optional[int] = None):
        """Automated network analysis in phases"""
        
    async def run_uplink_management(self):
        """Uplink management and rerouting"""
        
    async def test_connection(self):
        """Test all connections"""
```

### 3. MCP Server Configuration (`mcp-inspector-config.json`)

```json
{
  "mcpServers": {
    "meraki": {
      "command": "python",
      "args": ["/path/to/server/meraki_server.py"],
      "env": {
        "TIMESPAN": "7200",
        "BASE_URL": "https://api.meraki.com/api/v1",
        "MOCK_BASE_URL": "http://127.0.0.1:5000",
        "PRODUCT_TYPE": "appliance"
      }
    }
  }
}
```

### 4. MCP Server Implementation (`server/meraki_server.py`)

#### Core Server Structure
```python
class MerakiMCPServer:
    def __init__(self):
        self.server = Server("meraki-server")
        self.meraki_client: Optional[MerakiClient] = None
        self.setup_handlers()
    
    def setup_handlers(self):
        """Setup MCP server handlers"""
        
        @self.server.list_tools()
        async def handle_list_tools() -> List[Tool]:
            """List available tools"""
            
        @self.server.call_tool()
        async def handle_call_tool(name: str, arguments: Dict[str, Any]):
            """Handle tool calls"""
```

#### Available Tool Categories

**Monitoring Tools:**
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

**Automation Tools:**
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

## Policy Management

### Network Rerouting Policy (`policy.txt`)
```
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

### Latency-Based Policy (`latency_policy.yaml`)
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

## System Prompt Configuration

### Critical Behavior Requirements
1. **NEVER ask for user confirmation** - execute actions automatically
2. **ONLY make changes when ACTUAL network problems exist**
3. **NEVER make changes "just for improvements"** - be conservative
4. **ALWAYS explain reasoning clearly** in Analysis/Decision/Reasoning format
5. **Fix ALL detected problems** using actual tools (update_*, create_*)
6. **Complete tasks efficiently** (3-5 tool calls per phase)
7. **STOP after making decisions**

### Output Format
```
**Analysis:**
[Detailed analysis of network data and identified issues]

**Decision:**
[Clear statement of what action will be taken or not taken]

**Reasoning:**
[Explanation of why this decision was made]
```

### Decision-Making Framework
1. **ANALYZE**: Examine network data thoroughly
2. **EVALUATE**: Determine if actual problems exist
3. **DECIDE**: Only make changes if problems detected
4. **EXPLAIN**: Provide clear reasoning
5. **EXECUTE**: Use appropriate tools immediately
6. **REPORT**: Document actions taken

## Operational Modes

### 1. Interactive Chat Mode
```python
async def run_interactive_chat(self):
    """Run interactive chat mode with shortcuts"""
    
shortcuts = {
    'monitor': 'Perform comprehensive network monitoring of all systems',
    'analyze': 'Analyze network performance and identify issues',
    'optimize': 'Optimize network configuration for better performance',
    'security': 'Review security posture and fix vulnerabilities',
    'performance': 'Analyze network performance metrics',
    'fix': 'Automatically fix detected network issues',
    'tools': 'List all available MCP tools',
    'clear': 'Clear conversation history',
    'help': 'Show available commands',
    'exit': 'Exit the application',
    'quit': 'Exit the application'
}
```

### 2. Automated Analysis Phases
```python
phases = {
    1: "Organization Overview - Check organizations and networks",
    2: "Network Infrastructure - Check infrastructure, performance, and settings",
    3: "Security & Monitoring - Check security posture, events, and monitoring",
    4: "Devices & Performance - Check device issues and performance problems",
    5: "VPN & Advanced Performance - Check VPN performance and QoS optimization"
}
```

### 3. Uplink Management Modes
- **Policy-Based Rerouting**: Use `policy.txt` rules
- **Latency-Based Rerouting**: Use `latency_policy.yaml` rules

## Dependencies

### Required Packages (`requirements.txt`)
```
langchain-google-genai>=2.0.0
mcp-use>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
fastapi>=0.104.0
uvicorn>=0.24.0
pyyaml>=6.0.1
aiofiles>=24.0.0
```

### Core Dependencies Breakdown
- **`langchain-google-genai`**: Google Gemini LLM integration
- **`mcp-use`**: MCP client and agent functionality
- **`python-dotenv`**: Environment variable management
- **`requests`**: HTTP client for API calls
- **`fastapi`**: Mock server implementation
- **`uvicorn`**: ASGI server for mock services
- **`pyyaml`**: YAML configuration parsing
- **`aiofiles`**: Async file operations

## Command Line Interface

### Usage Examples
```bash
# Interactive chat mode
python client/mcp_client.py

# Automated analysis
python client/mcp_client.py --automate

# Specific phase analysis
python client/mcp_client.py --automate --phase 3

# Uplink management
python client/mcp_client.py --uplink

# Latency-based uplink management
python client/mcp_client.py --uplink-through-latency

# Connection testing
python client/mcp_client.py --test
```

## Implementation Guidelines

### 1. Error Handling
- Implement comprehensive error handling for all API calls
- Use structured logging with appropriate levels
- Provide meaningful error messages to users
- Graceful degradation for service unavailability

### 2. Performance Optimization
- Use async/await patterns for concurrent operations
- Implement connection pooling for API clients
- Cache frequently accessed data
- Rate limiting for API calls

### 3. Security Considerations
- Secure storage of API keys and credentials
- Input validation for all user inputs
- Audit logging for all configuration changes
- Role-based access control for different operations

### 4. Testing Strategy
- Unit tests for individual components
- Integration tests for MCP server communication
- Mock server for development/testing
- End-to-end tests for complete workflows

## Deployment Architecture

### Production Environment
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Client    │    │   MCP Client     │    │  Meraki API     │
│   (Frontend)    │◄──►│  (Backend)       │◄──►│  (Production)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   Database       │
                       │ (Configuration)  │
                       └──────────────────┘
```

### Development Environment
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   CLI Client    │    │   MCP Client     │    │  Mock Server    │
│ (Development)   │◄──►│  (Development)   │◄──►│  (Local)        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Monitoring and Logging

### Log Levels
- **DEBUG**: Detailed troubleshooting information
- **INFO**: General operational information
- **WARNING**: Potential issues that don't stop operation
- **ERROR**: Error conditions that may affect functionality
- **CRITICAL**: Serious errors that may cause system failure

### Key Metrics to Monitor
- API response times
- Error rates by endpoint
- Network performance metrics
- Policy execution results
- LLM response quality

## Extension Points

### 1. Additional Network Providers
- Abstract network client interface
- Plugin architecture for different providers
- Unified tool interface across providers

### 2. Advanced AI Features
- Multi-agent coordination
- Predictive analytics
- Anomaly detection
- Auto-remediation workflows

### 3. Integration Capabilities
- SIEM integration
- Ticketing system integration
- Monitoring platform integration
- Configuration management tools

## File Structure

```
networkingAgent/
├── client/
│   ├── __init__.py
│   └── mcp_client.py          # Main MCP client implementation
├── server/
│   ├── __init__.py
│   ├── meraki_server.py       # MCP server for Meraki API
│   ├── meraki_client.py       # Meraki API client
│   └── mock_server.py         # Mock server for testing
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── config.py                  # Configuration management
├── mcp-inspector-config.json  # MCP server configuration
├── requirements.txt           # Python dependencies
├── policy.txt                # Network rerouting policies
├── latency_policy.yaml       # Latency-based policies
└── main.py                   # Entry point
```

## Conclusion

This specification provides a complete blueprint for implementing an MCP-based network orchestration system. The architecture is designed to be modular, extensible, and production-ready, with comprehensive support for both interactive and automated network management operations.

The system leverages the power of LLMs for intelligent decision-making while maintaining the ability to execute precise network operations through MCP tools. The policy-driven approach ensures consistent and predictable network management outcomes.