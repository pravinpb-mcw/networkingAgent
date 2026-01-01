# Network Observability Agent System


Professional AI-powered network monitoring system with predictive failure detection and automated failover recommendations for Cisco Meraki networks.
## 🚀 **Key Features**

### 🧠 **Intelligent Uplink Rerouting**
- **Policy-Driven Automation**: Centralized policy file controls all rerouting decisions
- **Smart Load Balancing**: Automatically reroutes devices when WANs exceed 20-device limit
- **Down WAN Recovery**: Intelligently handles failed WANs by rerouting excess devices
- **Dynamic WAN Creation**: Creates WAN3 when all existing WANs are overloaded
- **Real-time Monitoring**: Continuous WAN status and device count monitoring

### 🤖 **AI-Powered Decision Making**
- **LLM Integration**: Uses Gemini 1.5 Flash for intelligent analysis
- **Natural Language Processing**: Understands and executes complex network commands
- **Context-Aware Actions**: Makes decisions based on complete network state
- **Zero Human Intervention**: Fully automated fixes with clear reasoning
- **Conservative Approach**: Only makes changes when actual problems exist

### 📊 **Comprehensive Network Analysis**
- **WAN Status Monitoring**: Real-time uplink health assessment
- **Device Distribution Analysis**: Intelligent counting and distribution logic
- **Capacity Management**: Automatic load balancing across available WANs
- **Performance Optimization**: Proactive network optimization

## 🏗️ **Architecture**

```
networkingAgent/
├── main.py                       # Main application entry point
├── start_phoenix.bat             # Start Phoenix observability server
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project configuration
│
├── 📁 phoenix/                   # Phoenix Observability System
│   ├── server.py                 # Phoenix server with auto-evaluation
│   ├── README.md                 # Phoenix documentation
│   ├── VALIDATION_GUIDE.md       # Client-facing validation guide
│   ├── validators/               # 5 deterministic validators (μ 1.00)
│   │   ├── tool_validators.py
│   │   ├── comprehensive_validators.py
│   │   └── input_output_validators.py
│   ├── utils/                    # Debug utilities
│   │   ├── check_math_failures.py
│   │   ├── check_risk_math.py
│   │   ├── check_tool_params.py
│   │   └── check_traces.py
│   └── .phoenix_data/            # SQLite database
│
├── 📁 agents/                    # AI Agent Modules
│   ├── agent_1_risk_calculation.py    # Risk score calculator
│   ├── agent_2_nearest_ap.py          # Nearest AP finder
│   └── agent_3_failover_suggestion.py # Failover decision maker
│
├── 📁 client/                    # MCP Client
│   └── mcp_client.py             # AI orchestration client
│
├── 📁 server/                    # MCP Server & Tools (100+ tools)
│   ├── get_wireless_health.py
│   ├── get_network_topology_link_layer.py
│   ├── update_risk_score.py
│   └── ... (100+ Meraki API tools)
│
├── 📁 scripts/                   # Utility Scripts
│   ├── batch/                    # Batch files (organized)
│   │   ├── run_all_agents.bat
│   │   ├── run_agent1_risk.bat
│   │   ├── run_agent2_nearest.bat
│   │   ├── run_agent3_failover.bat
│   │   ├── start_mock_server.bat
│   │   └── check_status.bat
│   └── (Python utility scripts)
│
├── 📁 agent_data/                # Agent Data Storage
│   ├── risk_scores.json          # Risk calculations
│   └── nearest_aps.json          # Nearest AP data
│
├── 📁 mock_data/                 # Test Data
│   └── comprehensive_api_data.json  # Network topology & metrics
│
├── 📁 policies/                  # Business Rules
│   └── network_policy.json       # Thresholds & rules
│
├── 📁 eval/                      # Original evaluation modules
└── 📁 core/                      # Core utilities
```
│   ├── update_appliance_settings.py # ⚙️ WAN creation tool
│   └── [other tools...]          # Additional network management tools
├── 📁 mock_data/                # Test Data & Configuration
│   └── comprehensive_api_data.json # 🗄️ Device & WAN test data
├── policy.txt                   # 📋 Centralized rerouting policies
├── requirements.txt             # 📦 Python dependencies
└── README.md                    # 📚 This documentation
```

## 🎯 **Core System: Uplink Rerouting**

### **How It Works**
1. **Policy Loading**: Reads centralized policies from `policy.txt`
2. **WAN Monitoring**: Checks WAN status via `get_network_settings`
3. **Device Analysis**: Counts devices per WAN via `get_organization_uplinks_statuses`
4. **Intelligent Decision**: LLM analyzes data and applies policies
5. **Automated Action**: Reroutes devices using `update_uplink` tool
6. **Dynamic Scaling**: Creates WAN3 when all WANs are overloaded

## 🛠️ **Quick Setup**

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Set API Key**
```bash
# Windows
set GEMINI_API_KEY=your_gemini_api_key_here

# Linux/Mac
export GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. **Start Mock Server** (Terminal 1)
```bash
python server/meraki_server.py
```
**Wait for**: `Mock Meraki server running on http://127.0.0.1:8000`

### 4. **Run Uplink Rerouting** (Terminal 2)
```bash
python client/mcp_client.py --uplink
```

## 🚀 **Usage Examples**

### **Uplink Rerouting System**
```bash
# Run intelligent uplink rerouting
python client/mcp_client.py --uplink

# The system will:
# 1. Check WAN status (WAN1, WAN2)
# 2. Count devices per WAN
# 3. Apply policies from policy.txt
# 4. Reroute devices if needed
# 5. Create WAN3 if all WANs overloaded
```

### **Other Network Analysis**
```bash
# Run comprehensive network analysis
python client/mcp_client.py --automate

# Interactive chat mode
python client/mcp_client.py
```

## 🚀 **Usage**

### **🧠 Uplink Rerouting System** (NEW!)
```bash
# Run intelligent uplink rerouting
python client/mcp_client.py --uplink

# The system will:
# 1. Check WAN status (WAN1, WAN2)
# 2. Count devices per WAN
# 3. Apply policies from policy.txt
# 4. Reroute devices if needed
# 5. Create WAN3 if all WANs overloaded
```

### **📊 Automated Network Analysis**
```bash
# Run all 4 phases automatically
python client/mcp_client.py --automate

# Run specific phase only
python client/mcp_client.py --automate --phase=1  # Organization overview
python client/mcp_client.py --automate --phase=2  # Infrastructure analysis
python client/mcp_client.py --automate --phase=3  # Security assessment
python client/mcp_client.py --automate --phase=4  # Device performance
```

### **💬 Interactive Chat Mode**
```bash
python client/mcp_client.py
```

## 🧠 **Intelligent Decision-Making**

### **Uplink Rerouting Framework** (NEW!)
The uplink rerouting system follows a policy-driven approach:

1. **POLICY LOAD**: Read centralized policies from `policy.txt`
2. **WAN MONITOR**: Check WAN status via `get_network_settings`
3. **DEVICE COUNT**: Count devices per WAN via `get_organization_uplinks_statuses`
4. **POLICY APPLY**: Apply rerouting rules based on device counts and WAN status
5. **EXECUTE**: Reroute devices using `update_uplink` tool
6. **SCALE**: Create WAN3 if all WANs exceed 20-device limit

### **Comprehensive Analysis Framework**
The general network analysis follows a structured decision-making process:

1. **ANALYZE**: Thoroughly examine network data and metrics
2. **EVALUATE**: Determine if there are actual problems or issues
3. **DECIDE**: Only make changes if problems exist and changes will improve the network
4. **EXPLAIN**: Always provide clear reasoning for decisions
5. **EXECUTE**: If changes are needed, use appropriate tools immediately
6. **REPORT**: Document what was checked, decisions made, and why

### **Behavior Rules**
- ✅ **NEVER asks for permission** - Takes action automatically
- ✅ **Only makes changes when actual problems exist**
- ✅ **Clear output format** - "NO CHANGES NEEDED." at end of report
- ✅ **Conservative approach** - When in doubt, doesn't make changes
- ✅ **Efficient execution** - Completes analysis in minimal steps
- ✅ **Policy-driven decisions** - All rerouting follows centralized policies

## 📊 **System Capabilities**

### **🧠 Uplink Rerouting System** (NEW!)
- **Policy-Driven**: Centralized `policy.txt` controls all rerouting decisions
- **Smart Load Balancing**: 20-device limit per WAN with excess device rerouting
- **Down WAN Recovery**: Handles failed WANs by rerouting only excess devices
- **Dynamic Scaling**: Creates WAN3 when all WANs exceed capacity
- **Real-time Monitoring**: Continuous WAN status and device count tracking

### **📊 Comprehensive Network Analysis**

#### **Phase 1: Organization Overview**
- **Tools Used**: `get_organizations`, `get_organization_networks`
- **Checks**: Organization structure, network count, configurations
- **Output**: Network overview and organizational health assessment

#### **Phase 2: Network Infrastructure**
- **Tools Used**: `get_organization_uplinks_statuses`, `get_network_settings`, `get_network_traffic`, `get_network_vpn_stats`
- **Checks**: Uplink connectivity, configuration issues, traffic bottlenecks, VPN performance
- **Output**: Infrastructure health and performance analysis

#### **Phase 3: Security & Monitoring**
- **Tools Used**: `get_network_events`, `get_login_security`, `get_security_intrusion`, `get_access_control_lists`
- **Checks**: Security vulnerabilities, unauthorized access, intrusion detection, access controls
- **Output**: Security posture assessment and automated fixes

#### **Phase 4: Devices & Performance**
- **Tools Used**: `get_network_clients`, `get_device_loss_and_latency_history`, `get_connectivity_monitoring`, `get_network_group_policies`
- **Checks**: Connected devices, performance issues, connectivity monitoring, policy configuration
- **Output**: Device health and policy optimization

## 🔧 **Available Tools**

### **🧠 Uplink Rerouting Tools** (NEW!)
- `get_network_settings` - **WAN status monitoring** (ok/down)
- `get_organization_uplinks_statuses` - **Device data collection** and counting
- `update_uplink` - **Device rerouting** between WANs (CORE TOOL)
- `update_appliance_settings` - **WAN creation** (WAN3, WAN4, etc.)

### **📊 Monitoring Tools**
- `get_network_clients` - Connected devices and usage patterns
- `get_network_traffic` - Traffic patterns and bandwidth utilization
- `get_device_loss_and_latency_history` - Performance metrics (latency, loss, jitter)
- `get_organization_vpn_stats` - VPN performance and statistics
- `get_network_events` - Network alerts and security events
- `get_network_group_policies` - User policies and bandwidth controls
- `get_organization_networks` - List all organization networks
- `get_connectivity_monitoring_destinations` - Connectivity monitoring
- `get_network_access_control_lists` - Access control rules
- `get_organization_login_security` - Authentication security
- `get_network_security_intrusion` - Intrusion detection settings

### **⚙️ Automation Tools**
- `update_network_settings` - Optimize network configuration
- `create_network_appliance_settings` - Configure infrastructure
- `create_network_wireless_settings` - Optimize WiFi/SSID configuration
- `update_network_group_policy` - Automate policy management
- `create_organization_network` - Automate network creation
- `update_connectivity_monitoring_destinations` - Optimize monitoring
- `update_network_access_control_lists` - Automate access control
- `update_organization_login_security` - Enhance authentication security
- `update_network_security_intrusion` - Automate security policies

## 📈 **Example Output**

### **🧠 Uplink Rerouting Example** (NEW!)
```
🚀 Running uplink analysis...

**POLICY FILE:**
NETWORK REROUTING UPLINK POLICIES
================================
1. WAN CAPACITY POLICY
   - Each WAN can handle maximum 20 devices
...

**Analysis:**
- WAN1: 25 devices (overloaded)
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
- DEVICES MOVED: 5 devices
```

### **📊 Comprehensive Analysis Example**
```
============================================================
✅ PHASE 1 COMPLETE
============================================================
**Analysis:**
The organization has 6 networks with appropriate configurations.

**Decision:**
No changes are needed.

**Reasoning:**
Network structure appears normal with no obvious issues.

**Report:**
- **Checked:** Organization networks and configurations
- **Decisions Made:** No changes were made
- **Reasoning:** Healthy and well-structured organization
- **NO CHANGES NEEDED.**
```

### **🔧 Automated Fixes Example**
```
============================================================
✅ PHASE 3 COMPLETE
============================================================
**Analysis:**
Found security vulnerabilities in login settings.

**Decision:**
Enabling secure port and updating login security.

**Reasoning:**
Security improvements will enhance network protection.

**Report:**
- **Checked:** Security settings and access controls
- **Decisions Made:** Enabled secure port, updated login security
- **Reasoning:** Security enhancements for better protection
```

## 🎯 **Benefits**

### **🧠 Uplink Rerouting Benefits** (NEW!)
- **Intelligent Load Balancing**: Automatically distributes devices across WANs
- **Zero-Downtime Failover**: Seamlessly handles WAN failures
- **Dynamic Scaling**: Creates new WANs when capacity is exceeded
- **Policy-Driven Decisions**: Centralized control over all rerouting logic
- **Real-time Optimization**: Continuous monitoring and adjustment

### **For Network Administrators**
- **70% reduction** in manual network management time
- **Proactive issue detection** before users are affected
- **Automated security enhancements** with clear reasoning
- **Comprehensive network health** assessment in minutes
- **Intelligent uplink management** with zero manual intervention

### **For Organizations**
- **Zero training required** - AI handles complex decisions
- **Consistent network optimization** across all locations
- **Reduced downtime** through proactive monitoring
- **Enhanced security posture** with automated improvements
- **Automatic load balancing** for optimal performance

### **For IT Teams**
- **Intelligent automation** that only makes necessary changes
- **Clear audit trail** of all decisions and actions
- **Scalable solution** for managing multiple networks
- **API quota management** with phased analysis approach
- **Policy-based control** for predictable behavior

## 🔒 **Security & Safety**

- **Conservative approach** - Only makes changes when problems exist
- **Clear reasoning** - Always explains why changes were made
- **Mock server testing** - Safe environment for development
- **API quota management** - Respects rate limits with delays
- **Comprehensive logging** - Full audit trail of all actions
- **Policy-driven control** - All rerouting follows centralized policies
- **Excess-only rerouting** - Only moves devices beyond capacity limits

## 🚀 **Getting Started**

### **Quick Start (Multi-Agent System)**
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set API key**: `export ANTHROPIC_API_KEY=your_key`
3. **Start all agents**: `python main.py`
4. **Check agent status**: `python scripts/check_agents.py`

### **Individual Agent Control**
```bash
python main.py --agent risk      # Agent 1: Risk Score calculation
python main.py --agent nearest   # Agent 2: Nearest AP recommendations  
python main.py --agent monitor   # Agent 3: Network monitoring (auto-starts dependencies)
```

**Note**: When starting the Network Monitoring Agent (Agent 3), it automatically starts the Risk Score Agent (Agent 1) and Nearest AP Agent (Agent 2) if they're not already running. This ensures seamless operation without manual dependency management.

### **Legacy Quick Start (Uplink Rerouting)**
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Set API key**: `export GEMINI_API_KEY=your_key`
3. **Start mock server**: `python server/meraki_server.py`
4. **Run rerouting**: `python client/mcp_client.py --uplink`

### **Full Setup (All Features)**
1. **Clone and setup** the repository
2. **Configure your API keys** in `.env`
3. **Start the mock server** for testing
4. **Run automated analysis** to see it in action
5. **Review the results** and understand the decisions

## 📚 **Documentation**

- **Quick Start**: See this README for immediate setup
- **Detailed Setup**: See `SETUP.md` for comprehensive instructions
- **Policy Configuration**: Edit `policy.txt` to customize rerouting rules
- **Tool Usage**: Check individual tool files for advanced usage
- **Examples**: Check the mock data for sample configurations

## 📞 **Support**

- **Issues**: Report bugs via GitHub Issues
- **Policy Questions**: Modify `policy.txt` for custom rerouting rules
- **API Issues**: Check environment variables and API keys

---

**Transform your network management with intelligent automation and smart uplink rerouting!** 🤖✨



.wenv\Scripts\python.exe agents\agent_3_failover_suggestion.py --continuous 10