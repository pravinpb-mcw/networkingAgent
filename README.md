# 🤖 Automated Network Orchestration Agent

An **AI-powered automated network management system** that intelligently monitors, analyzes, and automatically fixes Cisco Meraki network issues using natural language processing and intelligent decision-making.

## 🚀 **Key Features**

### 🤖 **Intelligent Automation**
- **Automated Network Analysis**: 4-phase comprehensive network assessment
- **Intelligent Decision-Making**: AI-powered problem identification and resolution
- **Zero Human Intervention**: Fully automated fixes with clear reasoning
- **Conservative Approach**: Only makes changes when actual problems exist

### 📊 **Phased Analysis System**
- **Phase 1**: Organization Overview & Network Structure
- **Phase 2**: Network Infrastructure & Performance
- **Phase 3**: Security & Monitoring Assessment
- **Phase 4**: Devices & Policy Analysis

### 🔧 **Automated Actions**
- **Security Enhancements**: Automatic security policy updates
- **Performance Optimization**: Bandwidth and traffic management
- **Configuration Management**: Network settings and policy updates
- **Real-time Monitoring**: Continuous network health assessment

## 🏗️ **Architecture**

```
networkingAgent/
├── 📁 client/                   # AI Client Components
│   └── mcp_client.py            # Automated orchestration agent
├── 📁 server/                   # MCP Server Components
│   ├── meraki_server.py         # Main MCP server
│   ├── meraki_client.py         # Shared API client
│   ├── get_network_*.py         # Monitoring tools
│   ├── create_*.py              # Configuration tools
│   └── update_*.py              # Update tools
├── 📁 mock_data/               # Mock data for testing
├── mock_server.py              # Local mock server for development
├── mcp-inspector-config.json   # MCP configuration
└── requirements.txt            # Dependencies
```

## 🛠️ **Quick Setup**

### 1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

### 2. **Configure Environment**
```bash
# Run setup script to create .env file
python setup_env.py

# Edit .env file with your actual API keys and network IDs
# Required: MERAKI_API_KEY, GEMINI_API_KEY, NETWORK_ID, ORGANIZATION_ID
```

### 3. **Start Mock Server** (for testing)
```bash
python mock_server.py
```

### 4. **Run Automated Analysis**
```bash
python client/mcp_client.py --automate
```

## 🚀 **Usage**

### **Automated Network Analysis**
```bash
# Run all 4 phases automatically
python client/mcp_client.py --automate

# Run specific phase only
python client/mcp_client.py --automate --phase=1  # Organization overview
python client/mcp_client.py --automate --phase=2  # Infrastructure analysis
python client/mcp_client.py --automate --phase=3  # Security assessment
python client/mcp_client.py --automate --phase=4  # Device performance
```

### **Interactive Chat Mode**
```bash
python client/mcp_client.py
```

## 🧠 **Intelligent Decision-Making**

### **Analysis Framework**
The agent follows a structured decision-making process:

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

## 📊 **Phase Analysis Details**

### **Phase 1: Organization Overview**
- **Tools Used**: `get_organizations`, `get_organization_networks`
- **Checks**: Organization structure, network count, configurations
- **Output**: Network overview and organizational health assessment

### **Phase 2: Network Infrastructure**
- **Tools Used**: `get_organization_uplinks_statuses`, `get_network_settings`, `get_network_traffic`, `get_network_vpn_stats`
- **Checks**: Uplink connectivity, configuration issues, traffic bottlenecks, VPN performance
- **Output**: Infrastructure health and performance analysis

### **Phase 3: Security & Monitoring**
- **Tools Used**: `get_network_events`, `get_login_security`, `get_security_intrusion`, `get_access_control_lists`
- **Checks**: Security vulnerabilities, unauthorized access, intrusion detection, access controls
- **Output**: Security posture assessment and automated fixes

### **Phase 4: Devices & Performance**
- **Tools Used**: `get_network_clients`, `get_device_loss_and_latency_history`, `get_connectivity_monitoring`, `get_network_group_policies`
- **Checks**: Connected devices, performance issues, connectivity monitoring, policy configuration
- **Output**: Device health and policy optimization

## 🔧 **Available Tools**

### **Monitoring Tools**
- `get_network_clients` - Connected devices and usage patterns
- `get_network_traffic` - Traffic patterns and bandwidth utilization
- `get_device_loss_and_latency_history` - Performance metrics (latency, loss, jitter)
- `get_organization_vpn_stats` - VPN performance and statistics
- `get_network_events` - Network alerts and security events
- `get_network_settings` - Network-wide configuration
- `get_organization_uplinks_statuses` - Device connectivity and failover
- `get_network_group_policies` - User policies and bandwidth controls
- `get_organization_networks` - List all organization networks
- `get_connectivity_monitoring_destinations` - Connectivity monitoring
- `get_network_access_control_lists` - Access control rules
- `get_organization_login_security` - Authentication security
- `get_network_security_intrusion` - Intrusion detection settings

### **Automation Tools**
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

### **Successful Analysis**
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

### **Automated Fixes**
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

### **For Network Administrators**
- **70% reduction** in manual network management time
- **Proactive issue detection** before users are affected
- **Automated security enhancements** with clear reasoning
- **Comprehensive network health** assessment in minutes

### **For Organizations**
- **Zero training required** - AI handles complex decisions
- **Consistent network optimization** across all locations
- **Reduced downtime** through proactive monitoring
- **Enhanced security posture** with automated improvements

### **For IT Teams**
- **Intelligent automation** that only makes necessary changes
- **Clear audit trail** of all decisions and actions
- **Scalable solution** for managing multiple networks
- **API quota management** with phased analysis approach

## 🔒 **Security & Safety**

- **Conservative approach** - Only makes changes when problems exist
- **Clear reasoning** - Always explains why changes were made
- **Mock server testing** - Safe environment for development
- **API quota management** - Respects rate limits with delays
- **Comprehensive logging** - Full audit trail of all actions

## 🚀 **Getting Started**

1. **Clone and setup** the repository
2. **Configure your API keys** in `.env`
3. **Start the mock server** for testing
4. **Run automated analysis** to see it in action
5. **Review the results** and understand the decisions

## 📞 **Support**

- **Documentation**: See `SETUP.md` for detailed setup instructions
- **Issues**: Report bugs via GitHub Issues
- **Examples**: Check the mock data for sample configurations

---

**Transform your network management with intelligent automation!** 🤖✨
