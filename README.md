# Cisco Meraki MCP Network Management Platform

A comprehensive Model Context Protocol (MCP) platform that provides AI-powered network management for Cisco Meraki networks through natural language interaction.

## 🚀 Features

### 🤖 AI-Powered Network Management
- **Natural Language Interface**: Manage networks using plain English
- **Intelligent Automation**: AI-driven network optimization and troubleshooting
- **Predictive Analytics**: Proactive network monitoring and alerts
- **Zero Learning Curve**: No technical knowledge required

### 📊 Network Monitoring Tools
- **Network Clients**: Get connected devices and usage patterns
- **Traffic Analysis**: Monitor bandwidth usage and application breakdown
- **Performance Metrics**: Device loss and latency history
- **VPN Statistics**: Organization-wide VPN performance data
- **Network Events**: Real-time network alerts and notifications
- **Uplink Status**: Device connectivity and failover information
- **Network Settings**: Complete network configuration overview
- **Group Policies**: User policy management and bandwidth controls
- **Organization Networks**: List and manage all networks in an organization
- **Connectivity Monitoring**: Monitor network connectivity destinations
- **Access Control Lists**: Network access control and security rules
- **Login Security**: Organization authentication and security policies
- **Security Intrusion**: Network intrusion detection and prevention

### ⚙️ Network Configuration Tools
- **Appliance Settings**: DHCP, VLAN, and network infrastructure
- **Wireless Settings**: WiFi/SSID configuration with smart traffic shaping
- **Group Policy Management**: Create, update, and delete user policies
- **Network Creation**: Create new networks with product types and timezone
- **Security Configuration**: Connectivity monitoring, access control, and intrusion prevention
- **Natural Language Converter**: Convert simple requests to complex API calls

## 🏗️ Architecture

```
networkingAgent/
├── 📁 server/                    # MCP Server Components
│   ├── meraki_server.py         # Main MCP server
│   ├── meraki_client.py         # Shared API client
│   ├── natural_language_converter.py  # AI-powered request converter
│   ├── get_network_*.py         # Monitoring tools
│   ├── create_*.py              # Configuration tools
│   └── update_*.py              # Update tools
├── 📁 client/                   # MCP Client Components
│   └── mcp_client.py           # Gemini-powered chat interface
├── 📁 mock_data/               # Mock data for testing
├── mock_server.py              # Local mock server for development
├── dashboard.py                # Web dashboard interface
├── network_monitor.py          # Network monitoring service
└── mcp-inspector-config.json   # MCP configuration
```

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Cisco Meraki Dashboard API access
- Google Gemini API key (for AI features)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd networkingAgent
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   # Create .env file
   cp .env.example .env
   ```

4. **Set up your configuration**
   ```env
   # Meraki API Configuration
   MERAKI_API_KEY=your_meraki_api_key
   NETWORK_ID=your_network_id
   ORGANIZATION_ID=your_organization_id
   SERIAL=your_device_serial
   IP=your_device_ip
   PRODUCT_TYPE=your_product_type
   TIMESPAN=86400

   # AI Configuration
   GEMINI_API_KEY=your_gemini_api_key

   # Optional: Mock server for testing
   USE_MOCK=true
   MOCK_BASE_URL=http://127.0.0.1:5000
   ```

## 🚀 Usage

### 1. Start the MCP Server
```bash
# Start the main MCP server
python server/meraki_server.py

# Or start with mock server for testing
USE_MOCK=true python server/meraki_server.py
```

### 2. Use the AI Chat Interface
```bash
# Start the Gemini-powered chat client
python client/mcp_client.py
```

### 3. Natural Language Examples

#### Network Monitoring
```
"Show me all devices connected to my network"
"Check network performance for the last 24 hours"
"Who's using the most bandwidth right now?"
"Are there any network issues today?"
```

#### Network Configuration
```
"Create a guest WiFi network with 500 Kbps limit"
"Block social media for the marketing team"
"Give video calls priority bandwidth"
"Optimize my network for tomorrow's conference"
"Create a new network called MCW Berlin Office with wireless and appliance products"
"Show me all networks in my organization"
"Add Google DNS as connectivity monitoring destination"
"Enable two-factor authentication for organization login"
"Set security intrusion mode to prevention"
```

#### Policy Management
```
"Update policy_1 with 1000 Kbps bandwidth limit"
"Enable traffic shaping for all guest policies"
"Create a new policy for remote workers"
```

### 4. Web Dashboard
```bash
# Start the web dashboard
python dashboard.py
```
Access at: `http://localhost:8000`

## 🔧 Configuration Options

### Routing Behavior
The platform uses intelligent routing based on HTTP methods:

- **GET requests** → Real Meraki API (live data)
- **POST/PUT/DELETE** → Mock server (safe testing)

### Environment Overrides
```env
# Force all requests to mock server
FORCE_MOCK_ALL=true

# Force all requests to real Meraki API
FORCE_REAL_ALL=true
```

## 🧪 Testing

### Mock Server
```bash
# Start mock server for development
python mock_server.py

# Test with mock data
python test_mock_server.py
```

### Test Tools
```bash
# Run specific tests
python test/test_tools.py
python test/test_config.py
```

## 📊 Available Tools

### Monitoring Tools
| Tool | Description | Endpoint |
|------|-------------|----------|
| `get_network_clients` | Connected devices and usage | `/networks/{id}/clients` |
| `get_network_traffic` | Traffic patterns and bandwidth | `/networks/{id}/traffic` |
| `get_device_loss_and_latency_history` | Performance metrics | `/devices/{serial}/lossAndLatencyHistory` |
| `get_organization_vpn_stats` | VPN statistics | `/organizations/{id}/appliance/vpn/stats` |
| `get_network_events` | Network alerts | `/networks/{id}/events` |
| `get_organization_uplinks_statuses` | Device connectivity | `/organizations/{id}/uplinks/statuses` |
| `get_network_settings` | Network configuration | `/networks/{id}/settings` |
| `get_network_group_policies` | User policies | `/networks/{id}/groupPolicies` |
| `get_organization_networks` | List all organization networks | `/organizations/{id}/networks` |
| `get_connectivity_monitoring_destinations` | Connectivity monitoring destinations | `/networks/{id}/appliance/connectivityMonitoringDestinations` |
| `get_network_access_control_lists` | Network access control lists | `/networks/{id}/switch/accessControlLists` |
| `get_organization_login_security` | Organization login security settings | `/organizations/{id}/loginSecurity` |
| `get_network_security_intrusion` | Network security intrusion settings | `/networks/{id}/appliance/security/intrusion` |

### Configuration Tools
| Tool | Description | Endpoint |
|------|-------------|----------|
| `update_network_settings` | Network configuration | `PUT /networks/{id}/settings` |
| `create_network_appliance_settings` | Network infrastructure | `POST /networks/{id}/appliance/settings` |
| `create_network_wireless_settings` | WiFi configuration | `POST /networks/{id}/wireless/settings` |
| `update_network_group_policy` | Policy management | `PUT /networks/{id}/groupPolicies/{policyId}` |
| `create_organization_network` | Create new network | `POST /organizations/{id}/networks` |
| `update_connectivity_monitoring_destinations` | Update connectivity monitoring | `PUT /networks/{id}/appliance/connectivityMonitoringDestinations` |
| `update_network_access_control_lists` | Update access control lists | `PUT /networks/{id}/switch/accessControlLists` |
| `update_organization_login_security` | Update login security settings | `PUT /organizations/{id}/loginSecurity` |
| `update_network_security_intrusion` | Update security intrusion settings | `PUT /networks/{id}/appliance/security/intrusion` |

## 🎯 Unique Selling Points

### For IT Managers
- **70% reduction** in network management time
- **Zero training** required for non-technical staff
- **Proactive monitoring** and automated alerts

### For CTOs
- **Future-proof** AI-first architecture
- **Vendor agnostic** design (extensible to other vendors)
- **Enterprise-ready** MCP framework

### For Business Users
- **Natural language** network management
- **Self-service** network operations
- **Instant insights** without technical knowledge

## 🔒 Security

- API keys stored securely in environment variables
- Mock server for safe testing of write operations
- Comprehensive error handling and logging
- Network isolation for sensitive operations

## 📈 Roadmap

- [ ] Multi-vendor support (Aruba, Ubiquiti, etc.)
- [ ] Voice command integration
- [ ] Mobile app development
- [ ] Advanced AI analytics
- [ ] Integration with ITSM platforms

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: See `SETUP.md` for detailed setup instructions
- **Issues**: Report bugs and feature requests via GitHub Issues
- **Discussions**: Join community discussions for questions and ideas

---

**Transform your network management with AI-powered simplicity!** 🚀
